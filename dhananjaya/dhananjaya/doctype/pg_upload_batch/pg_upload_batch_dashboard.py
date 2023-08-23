from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'heatmap': False,
		'fieldname': 'batch',
		'transactions': [
			{
				'label': _('References'),
				'items': ['Payment Gateway Transaction']
			}
		]
	}
