function create_data(graph_type,graph_title,array_labels,array_values,obj_setup,array_id_title,array_values_title){
	//get the max value out of the array_values
	var height_graph=obj_setup.graph_h;
	
	if(graph_type =='bar_stack'){
		var max_values=[];
		//get a range of colours for the stack
		var array_colors=getcolour_stages(html2rgb(obj_setup.x_axis_colour),html2rgb(obj_setup.y_axis_colour),array_values.length-1);
		for(i=0;i<array_values.length;i++){
			var total=0;
			$.each(array_values[i], function() {
		      total+=this;
		      return true;
		    });
			max_values.push(total);
		};
		var max_array=Math.max.apply( Math, max_values);
	}else{
		var max_values=[];
		for(i=0;i<array_values.length;i++){
			max_values.push(Math.max.apply( Math, array_values[i]));
		};
		var max_array=Math.max.apply( Math, max_values);
	}
	//turn off graph title
	graph_title='';
	if(max_array > 0){
		//if steps is not predefined
		if (obj_setup.predefined_steps != 0) {
			steps=obj_setup.predefined_steps;
			max_y=steps*Math.ceil(max_array/steps);
		}else{
			var steps=Math.ceil(height_graph/max_array);
			var steps_percent=Math.ceil(((10/height_graph)*100)/10)*10;
			steps=steps_percent;
			var max_y=(steps*Math.ceil(max_array/steps));	
			steps=max_y/steps;
		}
	}else{
		var steps=10;
		var max_y=100;
	}
	var array_pie=[];
	var size_3d=0;
	var obj_elements=[];
	if(graph_type == 'pie'){
		for(i=0;i<array_values[0].length;i++){
			if(array_values[0][i] >0){
				array_pie.push({"value": array_values[0][i],"label": array_labels[i] +":"+array_values[0][i]});	
			}
		}
		obj_elements[0]={
	      "type": graph_type,
	      "values":array_values[0] ,
	       "colours": [
	        obj_setup.x_axis_colour,
	        obj_setup.y_axis_colour
	      ],
	      "gradient-fill": true,
	  	  "start-angle": 35,
	  	  "values": array_pie
	    };
	}else{
		if(graph_type == 'bar_3d'){
			var size_3d=13;
			var bottom_colour='#E2E2E2';
		}else{
			var bottom_colour=obj_setup.x_axis_colour;
		}
		if(graph_type =='bar_stack'){
			array_keys=[];
			for(i=0;i<array_values_title.length;i++){
				array_keys.push({"colour":array_colors[i],"text":array_values_title[i],"font-size": 13});	
			}
			
			obj_elements[0]={
		      "type": graph_type,
			  "colours": array_colors,
		      "alpha":0.9,
		      "values":array_values,
		      "colour": obj_setup.x_axis_colour,
		      "keys": array_keys,
      		  "tip": "#x_label#:#val#<br>Total #total#"
		    };		
		}else{
			if(graph_type =='area'){
				var fill=obj_setup.x_axis_colour;
			}else{
				var fill='transparent';
			}
			for(x=0;x<array_values.length;x++){
				if(x % 2 == 0){
			       cl = obj_setup.x_axis_colour;
			    }else{
			       cl = obj_setup.y_axis_colour;
			    }
				obj_elements[x]={
			     "type": graph_type,
			     "alpha":1,
			     "values":array_values[x],
			     "colour": cl,
			     "text": array_values_title[x],
				 "fill": fill
			    };
			}	  
		}
		
		//console.log(array_keys);
	}
	var data = {
	  "elements": obj_elements,
	  "title": {
	    "text": graph_title
	  },
	  "x_axis": {
	    "3d":  size_3d,
	    "colour": bottom_colour,
	    "grid-colour": obj_setup.x_grid_colour,
	    "labels": {
	    	"labels": array_labels
	    }
	  },
	  "x_legend": {
	    "text": array_id_title[0],
	    "style": "{font-size: 12px; color: #000033}"
	    },
	  "y_axis": {
	    "colour": obj_setup.y_axis_colour,
	    "grid-colour": obj_setup.y_grid_colour,
	    "max": max_y,
	    "steps": steps
	  },
	  "bg_colour": obj_setup.bg_colour
	};
	
	return data;
}

function flash_chart_data(passed_string2){
	var re=new RegExp('[^0-9.]', "g");
	var passed_string = String(passed_string2);
	var passed_array=passed_string.split(',');
	var table_id=passed_array[0];
	var obj_setup={
		"bg_colour":passed_array[1],
		"y_grid_colour":passed_array[2],
		"y_axis_colour":passed_array[3],
		"x_axis_colour":passed_array[4],
		"x_grid_colour":passed_array[5],
		"graph_h":passed_array[6],
		"graph_w":passed_array[7],
		"chart_type":passed_array[8],
		"predefined_steps":0
	};
	var table_elm=$('#'+table_id);
	var the_var ='';
 	var th_count=table_elm.find("thead tr th").length;
 	var array_id_column=[];
 	var array_values_column=[];
 	var array_id=[];
 	var array_values=[];
 	var chart_type=obj_setup.chart_type;
 	var chart_name=table_elm.attr("summary");
 	var array_id_title=[];
 	var array_values_title=[];
	var array_values_stack=[];
	var split_regex=new RegExp("skip[0-9_]*");
	var steps_regex=new RegExp("steps_[0-9]*");
	var array_skip_row=[];
 	table_elm.find("thead tr th").each(function(i) {
		var the_classes=$(this).attr('class');
 		if($(this).hasClass("graph_id")){
 			array_id_column.push(i+1);
 			array_id_title.push($(this).attr("title"));
 		}
    	if($(this).hasClass("graph_value")){
 			array_values_column.push(i+1);
 			array_values_title.push($(this).attr("title"));
 		}
		if($(this).hasClass("graph_value_stack")){
			//has to be a stacked bar chart if stacked elements
			//chart_type='bar_stack';
			array_values_column.push(i+1);
			array_values_title.push($(this).attr("title"));
			array_values_stack.push(i+1);
		}

		if($(this).is("[class*='steps_']")){
			var step_num=steps_regex.exec(the_classes);
 			obj_setup.predefined_steps=parseInt(step_num[0].split('_')[1]);
			//obj_setup.predefined_steps=10;
 		}
		if(split_regex.test(the_classes)){
			var skip_pos=split_regex.exec(the_classes);
			if(skip_pos.index >-1){
				array_skip_row=skip_pos[0].substring(4).split('_');
		 	}
		}
 	});
	
 	var values_array_counter=-1;
	var b_made_stack_array=false;
 	for(i=1;i<=th_count;i++){
		var values_rows_array_counter=-1;
		do_push=false;
 		//create new sub array
 		if(jQuery.inArray(i,array_id_column) !=-1){
 			b_array_id=true;
 			b_array_values=false;
			do_push=true;
 		}
 		if(jQuery.inArray(i,array_values_column)!=-1){
 			//update the array counter
	    	values_array_counter+=1;

			if (jQuery.inArray(i, array_values_stack) != -1) {
				if(b_made_stack_array==false){
					var row_count=$(table_elm).find("tbody tr").size();
					for(p=0;p<row_count;p++){
						array_values[p]=[];	
					}
					b_made_stack_array=true;
				}
				b_stacked=true;
			}else{
				array_values[values_array_counter]=[];
				b_stacked=false;
			}
 			b_array_id=false;
 			b_array_values=true;
			do_push=true;
 		}
		if(do_push){
			table_elm.find("tbody tr td:nth-child("+i+")").each(function(x) {
				if(jQuery.inArray((x+1).toString(),array_skip_row) ==-1){
					if(b_array_id){
			 			array_id.push(jQuery.trim($(this).text()));
			 		}
					
			 		if(b_array_values){
						values_rows_array_counter+=1;
			 			//values must to numbers so strip any text
						if(b_stacked){
							//array_values[values_rows_array_counter].push(parseInt($(this).text().replace(re,'')));
							array_values[values_rows_array_counter].push(parseFloat($(this).text().replace(re,'')));
							
						}else{
							//array_values[values_array_counter].push(parseInt($(this).text().replace(re,'')));	
							array_values[values_array_counter].push(parseFloat($(this).text().replace(re,'')));	
						}
			 		}	
				}
		    });
		}
 	}
 	the_data=create_data(chart_type,chart_name,array_id,array_values,obj_setup,array_id_title,array_values_title);	
	return JSON.stringify(the_data);		
}
$(function() {
	var the_src='/static/ofc/ofc.swf';//default to current directory
	$(document.getElementsByTagName('script')).each(function(i) {
		var the_index=this.src.indexOf('openflashchart');
		if(the_index!=-1){
			var new_src=this.src;
			//new_src.substr(0,the_index+15);
			new_src=new_src.substr(0,the_index+15)+the_src;
			the_src=new_src;
			return false;
		}
	});
	//console.log(the_src);
	var flash_chart_path=the_src;
	var flash_div_name='flash_chart_';
	//default setup
	var flash_chart_h=300;
	var flash_chart_w=500;
	var flash_chart_bg='#ffffff';
	var	flash_chart_y_grid='#E2E2E2';
	var	flash_chart_y_axis='#000066';
	var	flash_chart_x_axis='#F65327';
	var	flash_chart_x_grid='#E2E2E2';
	var chart_type='bar';
	$(".graph_table").each(function(i) {
		//insert the div for the flash object	
		var current_name=flash_div_name+$(this).attr("id");
		$($(this)).after('<div id="'+current_name+'">You do not have flash installed - please go to: <a href="http://get.adobe.com/flashplayer/">http://get.adobe.com/flashplayer/</a> to install it</div>');
		//give the div the flash chart class so it can be read
		var current_el=$('#'+current_name);
		chart_type=get_chart_type(this);
		current_el.addClass("flash_chart_setup");
		if(current_el.css("background-image") !='none'){
			flash_chart_w=500;//parseInt(current_el.css("width"));
			flash_chart_h=parseInt(current_el.css("height"));
			flash_chart_bg=rgb2html(current_el.css("background-color"));
			flash_chart_y_grid=rgb2html(current_el.css("border-top-color"));
			flash_chart_y_axis=rgb2html(current_el.css("border-left-color"));
			flash_chart_x_axis=rgb2html(current_el.css("border-right-color"));
			flash_chart_x_grid=rgb2html(current_el.css("border-bottom-color"));
		}
		current_el.removeClass("flash_chart_setup");
		
		var pass_string=$(this).attr("id")+','+flash_chart_bg+','+flash_chart_y_grid+','+flash_chart_y_axis+','+flash_chart_x_axis+','+flash_chart_x_grid+','+flash_chart_h+','+flash_chart_w+','+chart_type;
		//add the flash to the page pointing at the table for its data
		//AllowScriptAccess
		var flashvars = {"get-data":"flash_chart_data","id":pass_string};
		var params = false;
		var attributes = {wmode: "Opaque",salign: "l",AllowScriptAccess:"always"};
		swfobject.embedSWF(flash_chart_path, current_name, flash_chart_w,flash_chart_h, "9.0.0", "/static/ofc/expressInstall.swf", flashvars, params, attributes );
		//now add the links to show a chart or data
		show_hide_chart($('#'+current_name),this);
	});
	$("a.flash_chart_link").click(function(event){
	  	event.preventDefault();
	    var the_id=$(this).attr("id").substr(16);
	    var flash_chart=$('#flash_chart_'+the_id);
	    if (flash_chart.is(":hidden")) {
	    	flash_chart.show();
	    	$(this).text("Hide chart");
	    }else{
	    	flash_chart.hide();
	    	$(this).text("Show chart");
	    }
	});
	$("a.html_table_link").click(function(event){
	  	event.preventDefault();
	    var the_id=$(this).attr("id").substr(16);
	    var html_table=$('#'+the_id);
	    if (html_table.is(":hidden")) {
	    	html_table.show();
	    	$(this).text("Hide table");
	    }else{
	    	html_table.hide();
	    	$(this).text("Show table");
	    }
	});
});

function flash_chart_reload(table_id) {
	//console.log(the_src);
	var flash_div_name='flash_chart_';
	//default setup
	var flash_chart_h=300;
	var flash_chart_w=500;
	var flash_chart_bg='#ffffff';
	var	flash_chart_y_grid='#E2E2E2';
	var	flash_chart_y_axis='#000066';
	var	flash_chart_x_axis='#F65327';
	var	flash_chart_x_grid='#E2E2E2';
	var chart_type='bar';
	$("#"+table_id+".graph_table").each(function(i) {
		//insert the div for the flash object
		var current_name=flash_div_name+table_id;
		//give the div the flash chart class so it can be read
		var current_el=$('#'+current_name);
		chart_type=get_chart_type(this);
		//current_el.addClass("flash_chart_setup");
		if(current_el.css("background-image") !='none'){
			flash_chart_w=500;//parseInt(current_el.css("width"));
			flash_chart_h=parseInt(current_el.css("height"));
			flash_chart_bg=rgb2html(current_el.css("background-color"));
			flash_chart_y_grid=rgb2html(current_el.css("border-top-color"));
			flash_chart_y_axis=rgb2html(current_el.css("border-left-color"));
			flash_chart_x_axis=rgb2html(current_el.css("border-right-color"));
			flash_chart_x_grid=rgb2html(current_el.css("border-bottom-color"));
		}
		//current_el.removeClass("flash_chart_setup");
		
		var pass_string=$(this).attr("id")+','+flash_chart_bg+','+flash_chart_y_grid+','+flash_chart_y_axis+','+flash_chart_x_axis+','+flash_chart_x_grid+','+flash_chart_h+','+flash_chart_w+','+chart_type;
		//add the flash to the page pointing at the table for its data
		//AllowScriptAccess
		var flashvars = {"get-data":"flash_chart_data","id":pass_string};
		var params = false;
		var attributes = {wmode: "Opaque",salign: "l",AllowScriptAccess:"always"};

		//swfobject.embedSWF(flash_chart_path, current_name, flash_chart_w,flash_chart_h, "9.0.0", "/static/ofc/expressInstall.swf", flashvars, params, attributes );

		var tmp = $("#"+current_name+">param[name=flashvars]")[0]

		var tmp = findSWF(current_name)
		tmp.reload();
		//tmp.reload("", false);
		//tmp.reload();

		//now add the links to show a chart or data
		//show_hide_chart($('#'+current_name),this);
	});
}



function rgb2html(rgb_string) {
	
	hex=rgb_string;
	if(hex.indexOf('#') == -1){
		//replace the rgb test etc with nothing, to leave the commas and numbers
		var re = new RegExp('[rgb(]|[)]|[ ]', "g");
		var triplet=rgb_string.replace(re,'').split(',');
		var hex = "#";
		for(var i=0;i<3;i++) {
			if(triplet[i] =='NaN'){
				triplet[i]=0;	
			}
			hex +=parseInt(triplet[i]).toString(16);
		}
		//console.log(triplet);
	}else{
		/*
		//make sure the hex string is full length
		if(hex.length<6){
			var new_hex=hex.substring(1,hex.length);
			add_char=new_hex.charAt(1);
			new_hex='#'+add_char+add_char+new_hex;
			console.log('new_hex'+new_hex);
		}
		*/
	}
	return(hex);
}
function html2rgb(h){
	var rgb='rgb(';
	for(i=1;i<h.length;i++){
		rgb+=parseInt(h.substring(i,i+2),16);
		if(i<5){
			rgb+=',';
		}
		i=i+1;
	}
	rgb+=')';
	return rgb;
}
function get_chart_type(table_el){
	var output='bar';
	if( $(table_el).is(".chart_type_pie") ) {
    	output='pie';
	}
	if( $(table_el).is(".chart_type_bar") ) {
    	output='bar';
	}
	if( $(table_el).is(".chart_type_bar_3d") ) {
    	output='bar_3d';
	}
	if( $(table_el).is(".chart_type_area") ) {
    	output='area';
	}
	if( $(table_el).is(".chart_type_line") ) {
    	output='line';
	}
	return output;
}
function show_hide_chart(flash_chart,html_table){
	var current_name=$(html_table).attr("id");
	$(html_table).before('<div class="show_hide_container"><div class="flash_chart_title">'+$(html_table).attr("summary")+'</div><a href="##" id="show_hide_flash_'+current_name+'" class="icon_link flash_chart_link">Show/hide chart</a><a href="##" id="show_hide_table_'+current_name+'" class="icon_link html_table_link">Show/hide table</a></div>');
	if ($(html_table).is(".chart_hidden")) {
		$(flash_chart).hide();
	}
	if ($(html_table).is(".table_hidden")) {
		$(html_table).hide();
	}
}
//utility method just to ge the colour stages
function getcolour_stages(start,end,stages){
	var array_colour=[];
	var re = new RegExp('[rgb(]|[)]|[ ]', "g");
	var start_array=start.replace(re,'').split(',');
	var end_array=end.replace(re,'').split(',');
	var pos =(1/stages).toFixed(1);
	for(i=0;i<stages;i++){
		var new_pos =pos*i;
    	array_colour.push(rgb2html("rgb(" + [
            Math.max(Math.min( parseInt((new_pos * (parseInt(end_array[0]) - parseInt(start_array[0]))) + parseInt(start_array[0])), 255), 0),
            Math.max(Math.min( parseInt((new_pos * (parseInt(end_array[1]) - parseInt(start_array[1]))) + parseInt(start_array[1])), 255), 0),
            Math.max(Math.min( parseInt((new_pos * (parseInt(end_array[2]) - parseInt(start_array[2]))) + parseInt(start_array[2])), 255), 0)
        ].join(",") + ")"));
	}
	return array_colour;
}
