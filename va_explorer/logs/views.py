
# Create your views here.
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse



import logging


from va_explorer.va_data_management.utils.logs import write_va_log

class Index(TemplateView):
    template_name = 'logs/index.html'

@method_decorator(csrf_exempt, name='dispatch')
class SubmitLog(TemplateView):
    template_name = 'logs/submit_log.html'
    logger = logging.getLogger("event_logger")
    
    def post(self, request, **kwargs):
        post_message = request.POST.get('message', None)
        if post_message:
            log_type = request.POST.get('name', "")
            print(f"writing {post_message} out to logger")
            write_va_log(self.logger, f"{[log_type]} {post_message}", request)
            return HttpResponse('logged click event')
