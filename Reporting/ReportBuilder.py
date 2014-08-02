"""
ReportBuilder: Compile a report/alert to be emailed to the user into an HTML formatted message.

Requires: 
"""
try:    # this is needed if we call any powermonitorweb classes because django doesn't know about pymysql
    import pymysql
    pymysql.install_as_MySQLdb()
except:
    pass
import os
# Aha! So this needs to be called because we are using django models outside of the django app.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecoberry.settings")
from ecoberry import settings
from Reporting.Mailer import Mailer
import DataAnalysis.PowerAlertScraper
from DataAnalysis.Plotting import Plotter
from DataAnalysis.Stats import UsageStats
from DataAnalysis.DataFrameCollector import DataFrameCollector
from powermonitorweb.models import AlertTip, User
from django.core.urlresolvers import reverse
from datetime import datetime
from dateutil.relativedelta import relativedelta
import socket


class ReportBuilder():
    """ReportBuilder"""

    def __init__(self):
        """Stuff to be initialized with class"""
        self._alert_scraper = DataAnalysis.PowerAlertScraper.PowerAlertScraper()
        self._mailer = Mailer()
        self._plotter = Plotter()
        self._usage_stats = UsageStats()
        self._collector = DataFrameCollector()
        self._ip = socket.gethostbyname(socket.gethostname())  # gets the network ip address of the pi

    def build_power_alert_report(self, power_alert_status):
        """Send an Eskom power alert to a user"""
        # needs: title name power_alert_status power_peak reporting_url image_url tips[]
        stats = None
        file_path = os.path.join(settings.BASE_DIR,'powermonitorweb', 'media', 'graphs', '')
        try:
            frame = self._collector.collect_period(period_type='hour',
                                                   period_start=str(datetime.now().replace(microsecond=0) - relativedelta(hours=1)), #TODO: Change this back to str(datetime.now().replace(microseconds=0) - relativedelta(hours=1))
                                                   period_length=1)
            stats = self._usage_stats.get_frame_stats(frame)
            self._plotter.plot_single_frame(data_frame=frame, title='Usage for last hour', y_label='Usage (kW)',
                                            x_label='Time', file_name=file_path + 'last_hour.png')
            del frame
        except:
            raise StandardError('Could not collect data')
        email_context = {}
        images = []

        email_context['power_alert_status'] = power_alert_status
        if email_context['power_alert_status'] == 'critical' or 'warning':
            email_context['title'] = "Power Alert Status %s" % email_context[
                'power_alert_status'].capitalize()
        else:
            return  # I don't think it's necessary to send "power's all fine chaps!"


        email_context['power_peak'] = stats['max']
        email_context['power_peak_time'] = stats['max_time']
        email_context['power_current'] = stats['end']
        # I'm guessing this is where it was intended to link to
        email_context['reporting_url'] = reverse('powermonitorweb:graphs')
        email_context['domain'] = self._ip
        email_context['graph_url'] = 'cid:graph'
        email_context['tips'] = AlertTip.objects.filter(id=1)  # TODO: Still need to work out how to query the reporting tips
        images.append(('graph', file_path + 'last_hour.png'))

        # build a report for each user
        mail_list = []
        for user in User.objects.all():
            if user.username != 'powermonitor':  # we don't want to email the sysadmin
                try:
                    email_context['name'] = user.first_name

                    # Add email to the mail list. All mails will be sent once all reports have been built
                    mail_list.append(self._mailer.create_multipart_mail(template_name='PowerAlert',
                                                                        email_context=email_context,
                                                                        subject=email_context['title'],
                                                                        recipients=[str(user.email),],
                                                                        images=tuple(images)))
                except:
                    raise StandardError('Could not create email for user %s' % user.first_name)
        self._mailer.send_emails(self._mailer.get_mail_list())  # send all the emails at once

    def build_usage_report(self, user, period_type, report_start, report_end):
        """Send a report of electricity consumption"""
        # needs: title name report_period report_begin report_end power_sum power_average image_url reporting_url
        email_context = {}
        images = []
        stats = None
        try:
            frame = self._collector.collect_period(period_start=report_start, period_end=report_end)
            self._plotter.plot_single_frame(data_frame=frame, title='Power Usage', y_label='Usage (kW)',
                                            x_label='Time', file_name='usage_report.svg')
            stats = self._usage_stats.get_frame_stats(data_frame=frame)
            del frame
        except:
            raise StandardError('Could not collect data')
        email_context['title'] = 'Usage Report from %s to %s' % (report_start, report_end)
        email_context['report_period'] = period_type
        email_context['report_start'] = report_start
        email_context['report_end'] = report_end
        email_context['power_sum'] = stats['total_usage']
        email_context['power_average'] = stats['average']
        email_context['image_url'] = 'cid:graph'
        email_context['reporting_url'] = reverse('powermonitorweb:graphs')

        email_context['name'] = user.first_name

        mail = self._mailer.create_multipart_mail(template_name='PowerAlert', email_context=email_context,
                                           subject=email_context['title'], recipients=[str(user.email), ],
                                           images=tuple(images))
        print mail
        self._mailer.send_emails(self._mailer.get_mail_list())


    def send_usage_alert(self, user, alert_event):  # TODO evaluate parameter choice here
        """Send an alert of electricity consumption"""
        # needs: title name power_peak power_average image_url reporting_url