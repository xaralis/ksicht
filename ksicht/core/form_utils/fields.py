from django.forms import EmailField as DjangoEmailField
from django.forms import FileField as DjangoFileField
from django.forms import ImageField as DjangoImageField

from .widgets import EmailInput, FileUploadInput


__all__ = ("EmailField", "FileField", "ImageField")


class EmailField(DjangoEmailField):
    widget = EmailInput()


class ImageField(DjangoImageField):
    widget = FileUploadInput()


class FileField(DjangoFileField):
    widget = FileUploadInput()
