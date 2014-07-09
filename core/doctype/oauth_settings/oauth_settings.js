

cur_frm.cscript.get_verification_code_for_calender= function(doc, dt, dn){
	console.log("in the verification_code");
	wn.call({
		method:"core.doctype.oauth_settings.oauth_settings.genearate_calendar_cred",
		args:{"client_id":doc.client_id,"client_secret":doc.client_secret,"app_name":doc.app_name},
		callback:function(r){
			window.open(r.message.authorize_url)
		}
	})
}

cur_frm.cscript.generate_token_calender = function(doc, dt ,dn){
	return wn.call({
			method: "core.doctype.oauth_settings.oauth_settings.generate_credentials",
			args: {
				"client_id":doc.client_id, 
				"client_secret":doc.client_secret, 
				"app_name":doc.app_name,
				"authorization_code": cur_frm.doc.verification_code_for_calender,
				"user_name":doc.user
			}
		});
}


cur_frm.cscript.allow_google_contact_access = function(doc, dt, dn) {
	console.log("in the allow");

	console.log([doc.client_id, doc.client_secret]);
		// , doc.scope, doc.user_agent, doc.application_redirect_uri])
	return wn.call({
		method: "core.doctype.oauth_settings.oauth_settings.get_google_authorize_url",
		args: {
			client_id: doc.client_id,
			client_secret: doc.client_secret,
			// scope:doc.scope,
			// user_agent: doc.user_agent,
			// application_redirect_uri: doc.application_redirect_uri
		},
		callback: function(r) {
			console.log("on js");
			console.log(r);
			console.log(r.message)
			window.open(r.message);
			// if(!r.exc) {
			// 	window.open(r.message);
			// }
		}
	});
}

cur_frm.cscript.generate_auth_tocken = function(doc, dt, dn) {
	console.log(doc.verification_code)
	return wn.call({
		method: "core.doctype.oauth_settings.oauth_settings.g_callback",
		args: {
			verification_code: doc.verification_code,
		// 	user_agent: doc.user_agent
		},
	});
}

cur_frm.cscript.read_contact = function(doc, dt, dn) {
	// console.log(doc.request_token)
	wn.call({
		method: "core.doctype.oauth_settings.oauth_settings.read_contact",
	});
}

