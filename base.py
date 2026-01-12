# forms/base.py
from django import forms


class BaseForm(forms.Form):
    """Base class for all non-model forms with consistent styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_form_styling()
    
    def apply_form_styling(self):
        """Apply CSS classes to all form fields"""
        for field_name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.Textarea):
                widget.attrs.update({
                    'class': 'form-textarea',
                    'rows': widget.attrs.get('rows', 3)
                })
            elif isinstance(widget, forms.Select):
                widget.attrs.update({
                    'class': 'form-select'
                })
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({
                    'class': 'form-checkbox'
                })
            elif isinstance(widget, forms.RadioSelect):
                widget.attrs.update({
                    'class': 'form-radio'
                })
            elif isinstance(widget, (forms.DateInput, forms.TimeInput)):
                widget.attrs.update({
                    'class': 'form-input'
                })
            else:
                widget.attrs.update({
                    'class': 'form-input'
                })


class BaseModelForm(forms.ModelForm):
    """Base class for all ModelForms with consistent styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_form_styling()
    
    def apply_form_styling(self):
        """Apply CSS classes to all form fields"""
        for field_name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.Textarea):
                widget.attrs.update({
                    'class': 'form-textarea',
                    'rows': widget.attrs.get('rows', 3)
                })
            elif isinstance(widget, forms.Select):
                widget.attrs.update({
                    'class': 'form-select'
                })
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.update({
                    'class': 'form-checkbox'
                })
            elif isinstance(widget, forms.RadioSelect):
                widget.attrs.update({
                    'class': 'form-radio'
                })
            elif isinstance(widget, forms.FileInput):
                widget.attrs.update({
                    'class': 'form-input'
                })
            elif isinstance(widget, (forms.DateInput, forms.TimeInput, forms.NumberInput)):
                widget.attrs.update({
                    'class': 'form-input'
                })
            else:
                widget.attrs.update({
                    'class': 'form-input'
                })
