from django import template

register = template.Library()

@register.filter
def is_image(file_name):
    return file_name.lower().endswith(('.jpg', '.jpeg', '.png'))

@register.filter
def is_document(file_name):
    return file_name.lower().endswith(('.pdf', '.doc', '.docx'))