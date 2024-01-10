// Copyright (c) 2023, Narahari Dasa and contributors
// For license information, please see license.txt

frappe.ui.form.on('Patron', {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frappe.call({
				'method': 'dhananjaya.dhananjaya.doctype.patron.patron.get_patron_status',
				'args': {
					'patron': frm.doc.name
				},
				'callback': function (res) {
					console.log(res);
					var template = frm.events.update_status_html(frm, res.message);
					frm.set_df_property('patron_status_html', 'options', template);
					frm.refresh_field('patron_status_html');
				}
			})
		}
	},
	update_status_html(frm, data) {

		// var html =	`<div style ="width:40vw; border: solid #26250f26;padding:10px; border-width:1px 10px ;border-radius: 10px 2px" >
		// 				<h3>Status</h3>
		// 				<div style="display:flex; justify-content: space-between;font-size:1em">
		// 					<div style = "width : 150px">Commited Donation</div>
		// 					<div style = "color:#ff15a4">${data['commited']}</div>
		// 				</div>
		// 				<div style="display:flex; justify-content: space-between;font-size:1em">
		// 					<div style = "width : 150px">Collected Donation</div>
		// 					<div style= "color:#448b00"> ${data['completed']}</div>
		// 				</div>
		// 				<hr>
		// 				<div style="display:flex; justify-content: space-between;font-size:1em">
		// 					<div style = "width : 150px">Remaining</div>
		// 					<div style= "color:#a57f00; font-weight:bold"> ${data['commited']-data['completed']}</div>
		// 				</div>
		// 			</div>
		// 			`
		// currency=""
		var formmated_amount = frm.events.formatMoney(data['commited']);
		console.log(formmated_amount);

		var html = `
		<div style="display: flex; justify-content: space-around; margin: 20px;">

			<div style="color:rgb(35 15 128);padding: 10px; border: 1px solid #ccc; border-radius: 5px; width: 30%;">
				<p>Committed Amount</p>
				<p style="font-weight: bold; margin-top: 10px;"> ${frm.events.formatMoney(data['commited'])}</p>
			</div>

			<div style="color:green; padding: 10px; border: 1px solid #ccc; border-radius: 5px; width: 30%;">
				<p>Completed Amount</p>
				<p style="font-weight: bold; margin-top: 10px;"> ${frm.events.formatMoney(data['completed'])}</p>
			</div>

			<div style="color:hsl(0deg 80.54% 32.36%); padding: 10px; border: 1px solid #ccc; border-radius: 5px; width: 30%;">
				<p>Remaining Amount</p>
				<p style="font-weight: bold; margin-top: 10px;"> ${frm.events.formatMoney(data['commited'] - data['completed'])}</p>
			</div>
		</div>

		`
		return html
	},
	formatMoney(amount) {
		return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount);
	}
});
