import sys, os

class GetXML(object):
	
    def __init__(self, config):

	declare_cat_titles = '$cat_titles = array(';
	declare_cat_types = '$cat_types = array(';
	declare_cat_algos = '$cat_algos = array(';
	#declare_cat_ids = '$cat_ids = array(';

	#cat_id = 0
	first_iteration = True
        for category in config.get('setup','categories').split(","):
	    cat_title = config.get(category,'cat_title')
	    cat_type  = config.get(category,'cat_type')
	    cat_algo  = config.get(category,'cat_algo')

	    if not first_iteration:
	        declare_cat_titles += ", ";
	        declare_cat_types += ", ";
		declare_cat_algos += ", ";
	        #declare_cat_ids += ", ";
	    else:
	        first_iteration = False

	    declare_cat_titles += "'" + category + "' => '" + cat_title + "'"
	    declare_cat_types  += "'" + category + "' => '" + cat_type  + "'"
	    declare_cat_algos  += "'" + category + "' => '" + cat_algo  + "'"
	    #declare_cat_ids    += "'" + category + "' => '" + str(cat_id) + "'"
	    #cat_id += 1

	declare_cat_titles += ');'
	declare_cat_types += ');'
	declare_cat_algos += ');'
	#declare_cat_ids += ');'

	web_title = config.get('setup','web_title')

	self.output = """<?php

	function curPageURL()
	{
	    $pageURL = 'http';
	    if ($_SERVER["HTTPS"] == "on") {$pageURL .= "s";}
	        $pageURL .= "://";
	    if ($_SERVER["SERVER_PORT"] != "80") {
	        $pageURL .= $_SERVER["SERVER_NAME"].":".$_SERVER["SERVER_PORT"].$_SERVER["REQUEST_URI"];
	    } else {
	        $pageURL .= $_SERVER["SERVER_NAME"].$_SERVER["SCRIPT_NAME"];
	    }

	    return $pageURL;
	}

	function getCatStatusXML($myModuleResultsArray)
	{
	    $pageURL = curPageURL();

	    """ + declare_cat_titles + "\n" + declare_cat_types + "\n" + declare_cat_algos + """

    # Get different categories with their type from the result Matrix
    $cat_modules = array();
	    $cat_info = array();
	    foreach ($myModuleResultsArray as $module=>$data) {
	        $date = date('Y-m-d', $data['timestamp']);
		$time = date('H:i', $data['timestamp']);
		$category = $data['category'];

	        if(!array_key_exists($category, $cat_info)) {
	            $cat_modules[$category] = '';
	            //$cat_info[$category]['name'] = $category;
	            $cat_info[$category]['title'] = $cat_titles[$category];
		    $cat_info[$category]['status'] = getCatStatus($category, $cat_algos[$category], $myModuleResultsArray);
		    $cat_info[$category]['type'] = $cat_types[$category];
		    $cat_info[$category]['link'] = "$pageURL?date=$date&amp;time=$time&amp;t=$category";
		}

		$cat_modules[$category] .= "  <module>\n";
		$cat_modules[$category] .= "   <name>$module</name>\n";
		$cat_modules[$category] .= "   <title>" . htmlentities($data['mod_title']) . "</title>\n";
		$cat_modules[$category] .= "   <type>" . $data['mod_type'] . "</type>\n";
		$cat_modules[$category] .= "   <status>" . $data['status'] . "</status>\n";
		$cat_modules[$category] .= "   <time>$date $time</time>\n";
		$cat_modules[$category] .= "   <link>$pageURL?date=$date&amp;time=$time&amp;t=$category&amp;m=$module</link>\n";
		$cat_modules[$category] .= "  </module>\n";
	    }

	    header('Content-Type: text/xml');
	    echo '<?xml version="1.0" encoding="ISO-8859-1"?>' . "\n";
	    echo '<happyface>' . "\n";
	    echo ' <title>' . htmlentities('""" + web_title + """') . '</title>' . "\n";
	    foreach ($cat_info as $category=>$info) {
	        echo ' <category>' . "\n";
	        echo '  <name>' . $category . '</name>' . "\n";
	        echo '  <title>' . htmlentities($info['title']) . '</title>' . "\n";
	        if($info['type'] != 'unrated')
	            echo '  <status>' . $info['status'] . '</status>' . "\n";
	        echo '  <type>' . $info['type'] . '</type>' . "\n";
	        echo '  <link>' . $info['link'] . '</link>' . "\n";

	        echo $cat_modules[$category];
	        echo ' </category>' . "\n";
	    }

	    echo '</happyface>';
	    exit;
	}

	if ($_REQUEST['action']=="getxml")
		getCatStatusXML($ModuleResultsArray);

	?>"""
