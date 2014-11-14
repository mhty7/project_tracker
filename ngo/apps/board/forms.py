from django import forms
from django.forms import extras
from datetime import datetime
import calendar
from django.forms import widgets
from datetime import date
from ngo.apps.board.models import *
from django.forms.formsets import BaseFormSet
from django.forms.models import BaseModelFormSet
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.functional import curry


YEARS=range(2010,date.today().year+20)

class DateSelectorWidget(widgets.MultiWidget):
    def __init__(self, attrs=None,years=None,days=None):
        MONTHS = {
            1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',
            5:'May', 6:'Jun', 7:'Jul', 8:'Aug',
            9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'
            }

        
        try :
            years = [(year, year) for year in years]
            #days = [(d, dd) for d,dd in days]
            months = [(month, MONTHS[month]) for month in range(1,13)]
        except ValueError:
            return ''

        _widgets = (
            widgets.Select(attrs=None, choices=years),
            widgets.Select(attrs=None, choices=months),
        )
        super(DateSelectorWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        try:
            if value:
                return [value.year,value.month,]
            return [None, None,]
        except AttributeError:
            dt = [int(x) for x in value.split("-")]
            return [dt[0],dt[1],]


    def format_output(self, rendered_widgets):
        widget_context={'year':rendered_widgets[0],'month':rendered_widgets[1],}
        return render_to_string('forms/datefield.html',widget_context)
        #return u''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        datelist = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            D = date(day=int(1), month=int(datelist[1]),
                    year=int(datelist[0]))
        except ValueError:
            return ''
        else:
            return str(D)


class ActivityDateForm(forms.Form):
    from_date=forms.DateField()
    to_date=forms.DateField()
    def __init__(self, *args, **kwargs):
        extra= kwargs.pop('extra')

        super(ActivityDateForm, self).__init__(*args, **kwargs)
        
        """
        arr={}
        for att in ('to_date','from_date'):
            if extra is None:
                y=2010
                m=1
            else:
                y=int(extra[att][1])
                m=int(extra[att][0])
            st,end=calendar.monthrange(y,m)
            days=range(1,end+1)
            weekdays=[]
            for d in days:
                if not weekdays:
                    weekdays.append((d,'%d' % 1))
                else:
                    if st%7==0:
                        weekdays.append((d,'%d' % int(st/7+1)))
                st=1+st
            arr[att]=weekdays
        """
        

        from_init=date(year=date.today().year,month=date.today().month,day=1)
        to_init=date(year=date.today().year,month=date.today().month,day=1)
        if not extra is None:
            from_init=date(year=int(extra['from_date'][1]),month=int(extra['from_date'][0]),day=int(extra['from_date'][2]))
            to_init=date(year=int(extra['to_date'][1]),month=int(extra['to_date'][0]),day=int(extra['to_date'][2]))
            


        self.fields['from_date'] = forms.DateField(widget=DateSelectorWidget(years=YEARS,))
        self.initial['from_date'] = from_init
        self.fields['to_date'] = forms.DateField(widget=DateSelectorWidget(years=YEARS,))
        self.initial['to_date'] = to_init

        if not extra is None and extra.get('editable',True)==False:
            self.fields['from_date'].widget.attrs['disabled'] = 'True'
            self.fields['to_date'].widget.attrs['disabled'] = 'True'

    def clean(self):
        cleaned_data=self.cleaned_data
        if type(self.fields['to_date'].widget) is forms.HiddenInput:
            pass
        else :
            fd=cleaned_data.get('from_date')
            td=cleaned_data.get('to_date')
            if (td-fd).days<0:
                raise forms.ValidationError('From date and To date must be in chronological order.')



        return cleaned_data





class BeneficiaryTypeForm(forms.ModelForm):
    class Meta:
        model=Beneficiary
        fields = ('ty',)
        widgets = {
            'ty': widgets.Select(attrs={'onchange': 'this.form.submit();',}),
        }    





class GroupForm(forms.ModelForm):
    FORM_NAME = "GroupForm"
    class Meta:
        model = BeneficiaryGroup
        fields = ('name',)

    def __init__(self,*args,**kwargs):
        #self.extra_args=kwargs.pop('extra_args',{})
        #self.request=extra_args.pop('request',None)
        #self.instance=kwargs['instance']
        self.user=kwargs.pop('user',None)
        super(GroupForm,self).__init__(*args,**kwargs)

    def save(self,commit=True):
        bengroup=super(GroupForm,self).save(commit=False)
        bengroup.user=self.user
        if commit:
            bengroup.save()
        return bengroup


class BeneficiaryRegisterForm(forms.ModelForm):
    FORM_NAME = "BeneficiaryRegisterForm"
    class Meta:
        model = Beneficiary
        fields = ('ty','lname','fname','group',)



    def __init__(self,*args,**kwargs):
        #self.extra_args=kwargs.pop('extra_args',{})
        #self.request=extra_args.pop('request',None)
        #self.instance=kwargs['instance']
        self.user=kwargs.pop('user',None)
        self.beneficiary = kwargs.get('instance', None)
        super(BeneficiaryRegisterForm,self).__init__(*args,**kwargs)

        if self.beneficiary:
            if self.beneficiary.group.all():
                bs= "<br />".join(['"'+str(b)+'"' for b in self.beneficiary.group.all()])
                bs="This user is among :<br />"+bs
            else:
                bs="This user belongs to no group."
            bs= bs+"<br />"+'To select, hold down "Control", or "Command" on a Mac, to select more than one.'
            self.fields['group'].help_text = bs
        else :
            bs='To select, hold down "Control", or "Command" on a Mac, to select more than one.'
            self.fields['group'].help_text = bs

        if self.user.beneficiaryGroup.count() ==0:
            self.fields['group'].widget = widgets.HiddenInput()
        self.fields['group'].queryset = self.user.beneficiaryGroup
        

    def save(self,commit=True):
        ben=super(BeneficiaryRegisterForm,self).save(commit=False)
        old=ben.id
        if old:
            pass
        else:
            ben.user=self.user
        
        old_save_m2m=self.save_m2m
        def save_m2m():
            old_save_m2m()
            ben.group.clear()
            for c in self.cleaned_data['group']:
                ben.group.add(c)

        self.save_m2m=save_m2m
        if commit:
            pass
            ben.save()
            self.save_m2m()
        return ben

class ActivityForm(forms.ModelForm):
    FORM_NAME = "ActivityForm"
    week1=forms.CharField(required=False,max_length=255,label='Week1')
    week2=forms.CharField(required=False,max_length=255,label='Week2')
    week3=forms.CharField(required=False,max_length=255,label='Week3')
    week4=forms.CharField(required=False,max_length=255,label='Week4')
    u_id = forms.IntegerField(widget=widgets.HiddenInput(),required=False)
    class Meta:
        model = Activity
        fields = ('activity_ty',)

    def __init__(self,*args,**kwargs):
        #self.extra_args=kwargs.pop('extra_args',{})
        #self.request=extra_args.pop('request',None)
        #self.instance=kwargs['instance']
        self.activity = kwargs.get('instance', None)
        self.user=kwargs.pop('user',None)
        super(ActivityForm,self).__init__(*args,**kwargs)

        if self.activity:
            for a in self.activity.description.all():
                if a.description :
                    if a.week=='1':
                        self.fields['week1'].initial = a.description
                    elif a.week=='2':
                        self.fields['week2'].initial = a.description
                    elif a.week=='3':
                        self.fields['week3'].initial = a.description
                    elif a.week=='4':
                        self.fields['week4'].initial = a.description

        if self.user:
            self.fields['u_id'].initial = self.user.id


    def save(self,fd,td):
        act=super(ActivityForm,self).save(commit=False)
        old=act.id

        act.fdate=fd
        act.tdate=td
        if old:
            pass
        else:
            act.user=self.user
        act.save()
        week1=self.cleaned_data['week1']
        week2=self.cleaned_data['week2']
        week3=self.cleaned_data['week3']
        week4=self.cleaned_data['week4']
        if old:
            for w in WEEK_CHOICES:
                try:
                    awd=act.description.get(week=w[0])
                    if w[0]=='1':
                        awd.description=week1
                    elif w[0]=='2':
                        awd.description=week2
                    elif w[0]=='3':
                        awd.description=week3
                    elif w[0]=='4':
                        awd.description=week4
                    awd.save()
                except:
                    continue
        else:
            awd1=ActivityWeeklyDescription(activity=act,week=1,description=week1)
            awd2=ActivityWeeklyDescription(activity=act,week=2,description=week2)
            awd3=ActivityWeeklyDescription(activity=act,week=3,description=week3)
            awd4=ActivityWeeklyDescription(activity=act,week=4,description=week4)
            awd1.save()
            awd2.save()
            awd3.save()
            awd4.save()
        return act


class BeneficiaryForm(forms.ModelForm):
    choice = forms.MultipleChoiceField(label="Week",
                choices=WEEK_CHOICES, widget=forms.CheckboxSelectMultiple,required=False)
    temp_id = forms.IntegerField(widget=widgets.HiddenInput(),required=False)

    class Meta:
        model = Beneficiary
        fields=('ty','lname','fname',)

    def __init__(self,*args,**kwargs):
        #self.extra_args=kwargs.pop('extra_args',{})
        #self.request=extra_args.pop('request',None)
        #self.instance=kwargs['instance']
        self.beneficiary = kwargs.get('instance', None)
        self.act=kwargs.pop('extra_args',None)
        super(BeneficiaryForm,self).__init__(*args,**kwargs)

        if self.beneficiary:
            self.fields['choice'].initial = self.beneficiary.activityWeek.filter(activity=self.act).values_list('week',flat=True)
                

    def clean(self):
        if(self._errors):
            raise forms.ValidationError('No empty fields is allowed.')
        return self.cleaned_data
    
    def save(self,act,user):
        ben=super(BeneficiaryForm,self).save(commit=False)
        old=ben.id
        tmp=self.cleaned_data.get('temp_id',None) or old
        if tmp :
            #no modify for user
            #modifing a beneficiary that other center might posses, from admin's view
            try:
                ben=Beneficiary.objects.get(id=tmp,user=user)
                ben.lname=self.cleaned_data['lname']
                ben.fname=self.cleaned_data['fname']
                ben.ty=self.cleaned_data['ty']
                ben.save()
            except:
                return
        else :
            #newly create ben associated with the user
            ben.user=user
            ben.save()
        

        #although we dont have any m2m involved attributes included in the fields...
        self.save_m2m()


        #ben.activity.add(act)
        
        #for aw in ben.activityWeek.filter(activity=act):
        #    ben.activityWeek.remove(aw)
        
        #ben.activityWeek.clear()
        cs = self.cleaned_data["choice"]
        for c in cs:
            awd=act.description.get(week=c)
            awd.beneficiaries.add(ben)

        return ben




class BeneficiaryAttendanceForm(forms.ModelForm):
    #center = forms.CharField(required=False,max_length=255,label='Center')
    choice = forms.MultipleChoiceField(label="Week",
                choices=WEEK_CHOICES, widget=forms.CheckboxSelectMultiple,required=False)
    class Meta:
        model = Activity
        #fields=('activity_ty','fdate','tdate',)
        fields=()

    def __init__(self,*args,**kwargs):
        #self.extra_args=kwargs.pop('extra_args',{})
        #self.request=extra_args.pop('request',None)
        #self.instance=kwargs['instance']
        self.activity = kwargs.get('instance', None)
        self.ben=kwargs.pop('extra_args',None)

        super(BeneficiaryAttendanceForm,self).__init__(*args,**kwargs)

        if self.activity and self.ben:
            #self.fields['center'].initial = self.activity.user.username
            self.fields['choice'].initial = self.ben.activityWeek.filter(activity=self.activity).values_list('week',flat=True)

    def save(self):
        #act=super(BeneficiaryAttendanceForm,self).save(commit=False)
        #old=act.id
        #act.save()

        #save before referencing it
        #since we didnt include id in it, the fact casting POST query on this form doesnt contain id will
        #cause an error


        for aw in self.ben.activityWeek.filter(activity=self.activity):
            self.ben.activityWeek.remove(aw)

        cs = self.cleaned_data["choice"]
        for c in cs:
            awd=self.activity.description.get(week=c)
            awd.beneficiaries.add(self.ben)

        return self.activity




class MyModelFormsetBase(BaseModelFormSet):
    extra_args=None
    def __init__(self,*args,**kwargs):
        self.extra_args=kwargs.pop('extra_args',None)
        subFormClass = self.form
        self.form = curry(subFormClass,extra_args=self.extra_args)
        super(MyModelFormsetBase,self).__init__(*args,**kwargs)



class RequiredModelFormSet(MyModelFormsetBase):
    def __init__(self, *args, **kwargs):
        super(RequiredModelFormSet,self).__init__(*args,**kwargs)
        for form in self.forms:
            form.empty_permitted = False
    def clean(self):
        if any(self.errors):
            return
        tmpids=[]
        for i in range(0,self.total_form_count()):
            form=self.forms[i]
            tmpid=form.cleaned_data['temp_id'] or (form.cleaned_data.get('id') and form.cleaned_data['id'].id)
            if tmpid is None :
                continue
            if tmpid in tmpids:
                raise forms.ValidationError("Beneficiaries in a set must have distinct IDs.")
            tmpids.append(tmpid)

        for i in range(0,self.total_form_count()):
            form=self.forms[i]
            choice=form.cleaned_data['choice']
            if not choice:
                raise forms.ValidationError("Each beneficiary needs to join at least in one week, Otherwise, remove the one from this event.")



class RequiredFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        super(RequiredFormSet,self).__init__(*args,**kwargs)
        for form in self.forms:
            form.empty_permitted = False
    def clean(self):
        if any(self.errors):
            return
        tmpids=[]
        for i in range(0,self.total_form_count()):
            form=self.forms[i]
            tmpid=form.cleaned_data['temp_id'] or (form.cleaned_data.get('id') and form.cleaned_data['id'].id)
            if tmpid is None :
                continue
            if tmpid in tmpids:
                raise forms.ValidationError("Beneficiaries in a set must have distinct IDs.")
            tmpids.append(tmpid)

        for i in range(0,self.total_form_count()):
            form=self.forms[i]
            choice=form.cleaned_data['choice']
            if not choice:
                raise forms.ValidationError("Each beneficiary needs to join at least in one week, Otherwise, remove the one from this event.")



class ActivityTypeForm(forms.Form):
    ACHOICE=(('0','Show All'),)+Activity.A_TYPE
    choice=forms.ChoiceField(choices=ACHOICE,)
    def __init__(self, *args, **kwargs):
        self.extra_args=kwargs.pop('extra_args',{})
        super(ActivityTypeForm, self).__init__(*args, **kwargs)
        self.fields['choice'].widget.attrs['onchange'] = 'this.form.submit();'
    def clean_choice(self):
        cleaned_data=self.cleaned_data
        data=cleaned_data.get('choice')
        if data==self.fields['choice'].choices[0][0]:
            data=None
        return data


class StatisticsForm(forms.Form):
    ACHOICE=(('0','Show All'),)+Activity.A_TYPE
    BCHOICE=(('0','Show All'),)+Beneficiary.B_TYPE
    achoice=forms.ChoiceField(choices=ACHOICE,)
    bchoice=forms.ChoiceField(choices=BCHOICE,)
    from_date=forms.DateField()
    f_week = forms.ChoiceField(choices=WEEK_CHOICES,)
    to_date=forms.DateField()
    t_week = forms.ChoiceField(choices=WEEK_CHOICES,)
    center=forms.ChoiceField()
    distinct=forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.extra_args=kwargs.pop('extra_args',{})
        super(StatisticsForm, self).__init__(*args, **kwargs)
        self.fields['from_date'].widget = DateSelectorWidget(years=YEARS,)
        self.fields['to_date'].widget = DateSelectorWidget(years=YEARS,)
        self.initial['from_date'] = date(year=date.today().year,month=date.today().month,day=1)
        self.initial['to_date'] = date(year=date.today().year,month=date.today().month,day=1)
        centers = User.objects.all().order_by('id').values_list("id", "username")
        self.fields['center'] = forms.ChoiceField(choices=centers)

    def clean(self):
        cleaned_data=self.cleaned_data

        fd=cleaned_data.get('from_date')
        td=cleaned_data.get('to_date')
        fw=cleaned_data.get('f_week')
        tw=cleaned_data.get('t_week')
        if fd==td:
            if int(tw)-int(fw)<0:
                raise forms.ValidationError('From date and To date must be in chronological order.')
        else:
            if (td-fd).days<0:
                raise forms.ValidationError('From date and To date must be in chronological order.')

        return cleaned_data




