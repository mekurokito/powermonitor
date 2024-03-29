from django.db import models
from django.contrib.auth.models import User
from powermonitorweb.fields import UnixTimestampField


class Readings(models.Model):
    """
    Stores electricity readings from the power monitoring circuit
    """
    time = UnixTimestampField(auto_now_add=True, auto_created=True, primary_key=True, null=False)
    reading = models.FloatField()


class Alert(models.Model):
    """
    Alert model. Stores descriptions for each alert.
    """
    # UserAlerts must be defined with quotes because the class is only defined after this class
    users = models.ManyToManyField(User, through='UserAlerts')
    alert_name = models.CharField(max_length=128)
    alert_description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.alert_description

class UserAlerts(models.Model):
    """
    Association class for Alert and UserProfile
    """
    user_id = models.ForeignKey(User)
    alert_id = models.ForeignKey(Alert)


class AlertTip(models.Model):
    """
    Tips for alerts
    """
    alerts = models.ManyToManyField(Alert)
    tip_description = models.CharField(max_length=255)

    def __unicode__(self):
        return self.tip_description


class Report(models.Model):
    """
    User reports. These are custom reports the user sets, and are different from the alerts
    """
    users = models.ManyToManyField(User, through='UserReports')
    report_type = models.CharField(max_length=128)

    def __unicode__(self):
        return self.report_type


class UserReports(models.Model):
    user_id = models.ForeignKey(User)
    report_id = models.ForeignKey(Report)
    occurrence_type = models.CharField(max_length=128)
    datetime = models.DateTimeField()
    report_daily = models.BooleanField()
    report_weekly = models.BooleanField()
    report_monthly = models.BooleanField()


class SocialMediaAccount(models.Model):
    """
    Social media account info for each user
    """
    user_id = models.ForeignKey(User)
    account_type = models.CharField(max_length=255)
    account_token = models.CharField(max_length=255)
    account_token_secret = models.CharField(max_length=255)
    account_auth_verify = models.CharField(max_length=255)
    post_daily = models.BooleanField()
    post_weekly = models.BooleanField()
    post_monthly = models.BooleanField()
    post_yearly = models.BooleanField()
    is_enabled = models.BooleanField()

    def __unicode__(self):
        return self.account_type


class Food(models.Model):
    """
    Food items. A list of all possible food products will be kept
    """
    food_description = models.CharField(max_length=255)
    food_spoiltime = models.TimeField()

    def __unicode__(self):
        return self.food_description


class HouseFoods(models.Model):
    """
    Food products for the household
    """
    food_id = models.ForeignKey(Food)


class ElectricityType(models.Model):
    """
    Setup what type of electricity plan the household has
    """
    plan_type = models.CharField(max_length=128)

    def __unicode__(self):
        return self.plan_type


class PrepaidTopups(models.Model):
    """
    Prepaid topups for the household
    """
    topup_date = models.DateTimeField(primary_key=True)
    topup_amount = models.FloatField()
    topup_units = models.IntegerField()


class PostPaid(models.Model):
    unit_cost = models.FloatField()


class Configuration(models.Model):
    """
    A class storing miscellaneous properties about the household
    """
    field = models.CharField(max_length=255, primary_key=True)
    value = models.IntegerField(default=0)


class EskomStats(models.Model):
    field = models.CharField(max_length=255, primary_key=True)
    value = models.CharField(max_length=255)
