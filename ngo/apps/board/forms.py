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

class DateSelectorWidget(widgets.MultiWidget):
    def __init__(self, attrs=None,years=None,days=None):
        MONTHS = {
            1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',
            5:'May', 6:'Jun', 7:'Jul', 8:'Aug',
            9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'
            }

        
        try :
            years = [(year, year) for year in years]
            days = [(d, dd) for d,dd in days]
            months = [(month, MONTHS[month]) for month in range(1,13)]
        except ValueError:
            return ''

        _widgets = (
            widgets.Select(attrs={'onchange': 'this.form.submit();'}, choices=years),
            widgets.Select(attrs={'onchange': 'this.form.submit();'}, choices=months),
            widgets.Select(attrs=None,choices=days),
        )
        super(DateSelectorWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        try:
            if value:
                return [value.year,value.month,value.day]
            return [None, None, None]
        except AttributeError:
            dt = [int(x) for x in value.split("-")]
            return [dt[0],dt[1],dt[2]]


    def format_output(self, rendered_widgets):
        widget_context={'year':rendered_widgets[0],'month':rendered_widgets[1],'week':rendered_widgets[2]}
        return render_to_string('forms/datefield.html',widget_context)
        #return u''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        datelist = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            D = date(day=int(datelist[2]), month=int(datelist[1]),
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
        

        from_init=date(year=date.today().year,month=date.today().month,day=1)
        to_init=date(year=date.today().year,month=date.today().month,day=1)
        if not extra is None:
            from_init=date(year=int(extra['from_date'][1]),month=int(extra['from_date'][0]),day=int(extra['from_date'][2]))
            to_init=date(year=int(extra['to_date'][1]),month=int(extra['to_date'][0]),day=int(extra['to_date'][2]))
            


        self.fields['from_date'] = forms.DateField(widget=DateSelectorWidget(years=range(2010,2030),days=arr['from_date']))
        self.initial['from_date'] = from_init
        self.fields['to_date'] = forms.DateField(widget=DateSelectorWidget(years=range(2010,2030),days=arr['to_date']))
        self.initial['to_date'] = to_init
        self.fields['prevtime_f']=forms.CharField(widget=widgets.HiddenInput(),initial=from_init.strftime('%m%d%Y'))
        self.fields['prevtime_t']=forms.CharField(widget=widgets.HiddenInput(),initial=to_init.strftime('%m%d%Y'))

        if not extra is None and extra.get('editable',True)==False:
            self.fields['from_date'].widget.attrs['disabled'] = 'True'
            self.fields['to_date'].widget.attrs['disabled'] = 'True'



class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        exclude=('user','fdate','tdate',)

class BeneficiaryForm(forms.ModelForm):
    temp_id = forms.IntegerField(widget=widgets.HiddenInput(),required=False)
    class Meta:
        model = Beneficiary
        exclude=('activity','user',)
        #widgets = {'id': widgets.HiddenInput()}

class BeneficiaryTypeForm(forms.ModelForm):
    class Meta:
        model=Beneficiary
        fields = ('ty',)
        widgets = {
            'ty': widgets.Select(attrs={'onchange': 'this.form.submit();',}),
        }    

class BeneficiaryAttendanceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        CHOICES = ((True, 'Attend',),(False, 'Not Attend',))
        super(BeneficiaryAttendanceForm, self).__init__(*args, **kwargs)
        self.fields['choice']=forms.ChoiceField(widget=widgets.RadioSelect,initial=True, choices=CHOICES, required=True)
        self.fields['id']=forms.IntegerField(widget=widgets.HiddenInput(),)
 

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

class RequiredModelFormSet(BaseModelFormSet):
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

