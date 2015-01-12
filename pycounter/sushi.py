"""NISO SUSHI support"""
from __future__ import absolute_import

from suds.client import Client
import pycounter.report
import six

def get_sushi_stats_raw(wsdlurl, start_date, end_date, requestor_id=None,
                        requestor_email=None, customer_reference=None,
                        report="JR1", release=4):
    """Get SUSHI stats for a given site in raw XML format.

    :param wsdlurl: URL to SOAP WSDL for this provider
    :param start_date: start date for report (must be first day of a month)
    :param end_date: end date for report (must be last day of a month)
    :param requestor_id: requestor ID as defined by SUSHI protocol
    :param requestor_email: requestor email address, if required by provider
    :param customer_reference: customer reference number as defined by SUSHI
        protocol
    :param report: report type, values defined by SUSHI protocol
    :param release: report release number (should generally be `4`.)

    """
    client = Client(wsdlurl)
    rdef = client.factory.create('ns1:ReportDefinition')

    rdef._Name = report
    rdef._Release = release
    rdef.Filters.UsageDateRange.Begin = start_date
    rdef.Filters.UsageDateRange.End = end_date

    cref = client.factory.create('ns1:CustomerReference')
    cref.ID = customer_reference

    reqr = client.factory.create('ns1:Requestor')
    reqr.ID = requestor_id
    if requestor_email is not None:
        reqr.Email = requestor_email

    report = client.service.GetReport(reqr, cref, rdef)

    return report


def get_report(*args, **kwargs):
    raw_report = get_sushi_stats_raw(*args, **kwargs)
    return _raw_to_full(raw_report)


def _raw_to_full(raw_report):
    """Convert a raw report to a pycounter.report.CounterReport object"""
    startdate = raw_report.ReportDefinition.Filters.UsageDateRange.Begin
    enddate = raw_report.ReportDefinition.Filters.UsageDateRange.End
    report_data = {}
    report_data['period'] = (startdate, enddate)
    
    report_data['report_version'] = raw_report.ReportDefinition._Release
    report_data['report_type'] = raw_report.ReportDefinition._Name

    report_data['customer'] = raw_report.Report.Report[0].Customer[0].Name
    report_data['institutional_identifier'] = raw_report.Report.Report[0].Customer[0].ID

    report_data['date_run'] = raw_report.Report.Report[0]._Created.date()

    report = pycounter.report.CounterReport()

    for k, v in six.iteritems(report_data):
        setattr(report, k, v)

    report.metric = pycounter.report.METRICS.get(report_data['report_type'])

    return report

