from django.views.generic import TemplateView

from va_explorer.utils.mixins import CustomAuthMixin


class Index(CustomAuthMixin, TemplateView):
    template_name = "home/index.html"


index = Index.as_view()

about = TemplateView.as_view(template_name="home/index.html")
