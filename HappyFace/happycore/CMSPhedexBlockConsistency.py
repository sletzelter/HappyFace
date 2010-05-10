##############################################
# PhEDEx Block Consistency module 
# Created: N.Ratnikova 09-10-09.
##############################################

from ModuleBase import *
from XMLParsing import *

class CMSPhedexBlockConsistency(ModuleBase):
    """
    Module to show results of the PhEDEx block consistency check.
    """
    def __init__(self,module_options):
        """
         Defines keys for the module database table.
        """
        ModuleBase.__init__(self,module_options)
        self.warning_limit = float(self.configService.get("setup",
                                                          "warning_limit"))
        self.old_result_warning_limit = float(self.configService.get("setup",
                                                          "old_result_warning_limit"))
        self.dsTag = 'consistency_xml_source'
        # Module table description:
        self.db_keys["buffer"] = StringCol(default=None)
        self.db_keys["application"] = StringCol(default=None)
        self.db_keys["test"] = StringCol(default=None)

        self.db_keys["starttime"] = StringCol(default=None)
        self.db_keys["endtime"] = StringCol(default=None)
        self.db_keys["duration"] = StringCol(default=0)
        self.db_keys["warning_limit"] = FloatCol(default=self.warning_limit)

        self.db_keys["technology"] = StringCol(default=None)
        self.db_keys["protocol"] = StringCol(default=None)
        self.db_keys["dumpfile"] = StringCol(default=None)

        self.db_keys["total_datasets"] = IntCol(default=0)
        self.db_keys["total_blocks"] = IntCol(default=0)
        self.db_keys["total_files"] = IntCol(default=0)

        self.db_keys["failed_datasets"] = IntCol(default=0)
        self.db_keys["failed_blocks"] = IntCol(default=0)
        self.db_keys["failed_files"] = IntCol(default=0)

        self.db_keys["total_size"] = StringCol(default=None)

	############################################################
	# Dump detailed information about files into details table
	self.details_database = self.__module__ + "_table_details"

    def __old_result__(self):
        # Get starttime in unix format from the name of the dumpfile:
        tmp=os.path.basename(self.db_values["dumpfile"])
        # Convert result age into hours:
        result_age = (float(self.timestamp) - float(tmp.split('.')[0]))/3600.0
        if (result_age > self.old_result_warning_limit):
            return self.old_result_warning_limit

    def process(self):
        """
        Downloads input source xml file.
        Parses xml document and saves data in the database.
        Defines algorithm for module status.
        """

        dl_error,sourceFile = self.downloadService.getFile(self.getDownloadRequest(self.dsTag))
	source_tree,xml_error = XMLParsing().parse_xmlfile_lxml(sourceFile)
	root = source_tree.getroot()

        ###############################################################
        for data in root:
            if data.tag == "test_summary":
                for element in data.iter():
                    if element.tag == "application":
                        element_attrib = element.attrib
                        self.db_values["buffer"] =  element_attrib["buffer"]
                        self.db_values["application"] =  element_attrib["name"]
                        self.db_values["test"] =  element_attrib["test"]

                        self.db_values["starttime"] = element_attrib["starttime"]
                        self.db_values["endtime"] = element_attrib["endtime"]
                        self.db_values["duration"] = element_attrib["duration"]

                        self.db_values["technology"] =  element_attrib["technology"]
                        self.db_values["protocol"] =  element_attrib["protocol"]
                        self.db_values["dumpfile"] =  element_attrib["dump"]

                    if element.tag == "total":
                        element_attrib = element.attrib
                        self.db_values["total_datasets"] =  int(element_attrib["datasets"])
                        self.db_values["total_blocks"] =  int(element_attrib["blocks"])
                        self.db_values["total_files"] =  int(element_attrib["lfns"])
                        self.db_values["total_size"] =  element_attrib["size"]

                    if element.tag == "number_of_affected":
                        element_attrib = element.attrib
                        self.db_values["failed_datasets"] =  int(element_attrib["datasets"])
                        self.db_values["failed_blocks"] =  int(element_attrib["blocks"])
                        self.db_values["failed_files"] =  int(element_attrib["files"])


        # Details table description:
	details_db_keys = {}

        details_db_keys["lfn"] = StringCol()
        details_db_keys["status"] = StringCol()
        details_db_keys["dataset"] = StringCol()
        details_db_keys["block"] = StringCol()

	my_subtable_class = self.table_init( self.details_database, details_db_keys )

        # Fill in the values:
	details_db_values = {}

        for data in root:
            if data.tag == "details":
                for element in data.iter():
                    if element.tag == "file":
                        element_attrib = element.attrib
                        details_db_values["lfn"] =  element_attrib["name"]
                        details_db_values["status"] =  element_attrib["status"]
                        details_db_values["dataset"] =  element_attrib["dataset"]
                        details_db_values["block"] =  element_attrib["block"]
                        # write details to databse

                        self.table_fill( my_subtable_class, details_db_values )
	self.subtable_clear(my_subtable_class, [], self.holdback_time)

        

        ################################
        # Rating algorithm
        # Status legend:
        #  1.0  = success
        #  0.5  = warning # duration and/or result age exceed warning limit
        #  0.0  = error   # at least one dataset failed
        self.status = 1.0
        #------------------------------
        # Warning conditions definition:
        duration=float(self.db_values["duration"])
        if duration > self.warning_limit:
            self.status = 0.5
        if (self. __old_result__()):
            self.status = 0.5
        #------------------------------
        # Error condition definition:
        failed_datasets=int(self.db_values["failed_datasets"])
        if failed_datasets > 0:
            self.status = 0.0

    def output(self):
	""" Creates module contents for the web page, filling in
        the data from the database.
        """

	mc_begin = []

        # Predefine warnings to be inserted in output:
        warning_color=""
        if (self.__old_result__()):
            mc_begin.append('<p class="CMSPhedexBlockConsistencyWarningMessage"> WARNING: Result is older than ' + str(self.__old_result__()) + ' hours</p>')
            warning_color=' class="warning"'

	mc_begin.append(  '<table class="TableDataSmall">')
	mc_begin.append(  ' <tr class="TableHeader">')
	mc_begin.append(  '  <td>Buffer:</td>')
        mc_begin.append("""  <td>' . $data["buffer"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Application:</td>')
	mc_begin.append("""  <td>' . $data["application"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Test:</td>')
	mc_begin.append("""  <td>' . $data["test"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr' + warning_color + '>')
	mc_begin.append(  '  <td>Started:</td>')
	mc_begin.append("""  <td>' . $data["starttime"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Ended:</td>')
	mc_begin.append("""  <td>' . $data["endtime"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(""" <tr' . $duration_color . '>""")
	mc_begin.append(  '  <td>Duration:</td>')
        mc_begin.append("""  <td>' . $data["duration"] . ' hours<br />warning limit: ' . $data["warning_limit"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Total size:</td>')
	mc_begin.append("""  <td>' . $data["total_size"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Technology:</td>')
	mc_begin.append("""  <td>' . $data["technology"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Protocol:</td>')
	mc_begin.append("""  <td>' . $data["protocol"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <!--')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Input file:</td>')
	mc_begin.append("""  <td>' . $data["dumpfile"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  '  -->')
	mc_begin.append(  '</table>')
	mc_begin.append(  '<br />')
	mc_begin.append(  '')
	mc_begin.append(  '<table class="TableDataSmall">')
	mc_begin.append(  ' <tr class="TableHeader">')
	mc_begin.append(  '  <td>Tested:</td>')
	mc_begin.append(  '  <td>Datasets:</td>')
	mc_begin.append(  '  <td>Blocks:</td>')
	mc_begin.append(  '  <td>Files:</td>')
	mc_begin.append(  ' </tr>')
	mc_begin.append(  ' <tr>')
	mc_begin.append(  '  <td>Total:</td>')
	mc_begin.append("""  <td>' . $data["total_datasets"] . '</td>""")
	mc_begin.append("""  <td>' . $data["total_blocks"] . '</td>""")
	mc_begin.append("""  <td>' . $data["total_files"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(""" <tr ' . $status_color . '>""")
	mc_begin.append(  '  <td>Failed:</td>')
	mc_begin.append("""  <td>' . $data["failed_datasets"] . '</td>""")
	mc_begin.append("""  <td>' . $data["failed_blocks"] . '</td>""")
	mc_begin.append("""  <td>' . $data["failed_files"] . '</td>""")
	mc_begin.append(  ' </tr>')
	mc_begin.append(  '</table>')
	mc_begin.append(  '<br />')
	mc_begin.append(  '')
	mc_begin.append("""<input type="button" value="show/hide Failed Datasets" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__ + """_datasets_details\\\');" />""")
	mc_begin.append(  '<div class="DetailedInfo" id="' + self.__module__ + '_datasets_details" style="display:none;">')
	mc_begin.append(  ' <table class="TableDetails">')
	mc_begin.append(  '  <tr class="TableHeader">')
	mc_begin.append(  '   <td>Dataset</td>')
	mc_begin.append(  '   <td>Failed Blocks</td>')
	mc_begin.append(  '   <td>Failed Files</td>')
	mc_begin.append(  '  </tr>')

	mc_row = []
	mc_row.append(    '  <tr>')
	mc_row.append(  """   <td>' . $info["dataset"] . '</td>""")
	mc_row.append(  """   <td>' . $info["blocks"] . '</td>""")
	mc_row.append(  """   <td>' . $info["files"] . '</td>""")
	mc_row.append(    '  </tr>')

	mc_mid = []
	mc_mid.append(    ' </table>')
	mc_mid.append(    '</div>')
	mc_mid.append(    '<br />')

	mc_mid.append(  """<input type="button" value="show/hide Inconsistent Files" onfocus="this.blur()" onclick="show_hide(\\\'""" + self.__module__ + """_files_details\\\');" />""")
	mc_mid.append(    '<div class="DetailedInfo" id="' + self.__module__ + '_files_details" style="display:none;">')
	mc_mid.append(    ' <table class="TableDetails">')
	mc_mid.append(    '  <tr class="TableHeader">')
	mc_mid.append(    '   <td>Logical File Name</td>')
	mc_mid.append(    '   <td>Status</td>')
	mc_mid.append(    '  </tr>')

	mc_detailed_row = []
	mc_detailed_row.append(  '  <tr>')
	mc_detailed_row.append("""   <td>' . $info["lfn"] . '</td>""")
	mc_detailed_row.append("""   <td>' . $info["status"] . '</td>""")
	mc_detailed_row.append(  '  </tr>')

	mc_end = []
	mc_end.append(    ' </table>')
	mc_end.append(    '</div>')
	mc_end.append(    '<br />')

	module_content = """<?php

        if ($data["status"] == "1.0")
            $status_color=' class="ok"';
        elseif ($data["status"] == "0.0")
            $status_color=' class="critical"';

        if ($data["duration"] >= $data["warning_limit"])
            $duration_color=' class="warning"';

	print('""" + self.PHPArrayToString(mc_begin) + """');
        
	$details_db_sqlquery = "SELECT dataset, count(distinct block) as blocks, count(distinct lfn) as files FROM """+self.details_database+""" WHERE timestamp = " . $data["timestamp"] . " group by dataset";
        
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		print('""" + self.PHPArrayToString(mc_row) + """');
	}

	printf('""" + self.PHPArrayToString(mc_mid) + """');

	$details_db_sqlquery = "SELECT * FROM """+self.details_database+""" WHERE timestamp = " . $data["timestamp"];
	foreach ($dbh->query($details_db_sqlquery) as $info)
       	{
		print('""" + self.PHPArrayToString(mc_detailed_row) + """');
	}

	print('""" + self.PHPArrayToString(mc_end) + """');

	?>"""

	return self.PHPOutput(module_content)
