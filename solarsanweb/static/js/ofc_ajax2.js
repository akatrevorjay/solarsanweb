function reload() {
	if (timerID) {
		clearTimeout(timerID);
	}

	Dajaxice.solarsan.graph_utilization(reload_callback);
}

function reload_callback(data) {
	// Dajax.process(data);

	tmp = findSWF("graph_utilization");
	//alert(data)
    //x = tmp.load( JSON.stringify(data) );
    x = tmp.load( JSON.stringify(data) );

	timerID  = setTimeout("reload()", 3000);
}

function findSWF(movieName) {
	if (navigator.appName.indexOf("Microsoft")!= -1) {
		return window[movieName];
	} else {
		return document[movieName];
	}
}

