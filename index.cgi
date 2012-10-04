#!/usr/bin/perl -w -T
#======================================================================
#
#       psTracerouteViewer index.cgi
#       $Id: index.cgi,v 1.2 2012/10/03 23:20:34 dwcarder Exp $
#
#       A cgi for viewing traceroute data stored in PerfSonar.
#
#       Written by: Dale W. Carder, dwcarder@wisc.edu
#       Network Services Group
#       Division of Information Technology
#       University of Wisconsin at Madison
#
#       Inspired in large part by traceroute_improved.cgi by Yuan Cao <caoyuan@umich.edu>
#
#       Copyright 2012 The University of Wisconsin Board of Regents
#       Licensed and distributed under the terms of the Artistic License 2.0
#
#       See the file LICENSE for details or reference the URL:
#        http://www.perlfoundation.org/artistic_license_2_0
#
#======================================================================

#TODO select timezone
#TODO select measurement archive from a list


#======================================================================
#    C O N F I G U R A T I O N   S E C T I O N
#

my $Script = 'index.cgi';
my $URLPath = "/toolkit/gui/services/psTracerouteViewer";
my $Default_mahost = 'localhost:8086/perfSONAR_PS/services/tracerouteMA';
my $Ver = 'psTracerouteViewer $Id: index.cgi,v 1.2 2012/10/03 23:20:34 dwcarder Exp $';

#
#======================================================================
#======================================================================
#       U S E   A N D   R E Q U I R E

use lib "/opt/perfsonar_ps/toolkit/web/root/gui/services/psTracerouteViewer";
use strict;
use psTracerouteUtils;
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);
use Date::Manip;
use Socket;
use Socket6;
use Data::Validate::IP qw(is_ipv4 is_ipv6);
use Data::Dumper;

#
#======================================================================


#======================================================================
#       F U N C T I O N   P R O T O T Y P E S

sub parseInput();
sub lookup($;$);
sub displayTrData();
sub displayTop();
sub displaySelectBox();

#
#======================================================================


#======================================================================
#       G L O B A L S
my $mahost;     # measurement archive host url
my $stime;      # start time passed in 
my $etime;      # end time passed in 
my $epoch_stime;        # start time in unix epoch
my $epoch_etime;        # end time in unix epoch
my %endpoint;   # measurement endpoints
my $epselect;   # endpoint selection
my $donotdedup; # deduplication checkbox
my %dnscache;   # duh

#
#======================================================================



#======================================================================
#       M A I N 

parseInput();

my $ma_result = GetTracerouteMetadataFromMA($mahost,$epoch_stime,$epoch_etime);
ParseTracerouteMetadataAnswer($ma_result,\%endpoint);


# print http header
print("Content-Type: text/html;\n\n");


displayTop();

if ( scalar(keys((%endpoint))) < 1 ) {
        print "<b><font color=\"red\">Error: No Measurement Archives available.</font></b>\n<br>\n";

} else {

        displaySelectBox(); 

   	if ($epselect ne 'unselected') {
        	displayTrData();
	}
}

print "<br><br><hr>$Ver<br>\n";

exit();



#=============  B E G I N   S U B R O U T I N E S  =============================


# Sanity Check all cgi input, and set defaults if none are given
sub parseInput() {

        # measurement archive url
        if (defined(param("mahost"))) {
                if (param("mahost") =~ m/^[0-9a-zA-Z\/:_]+$/) {
                         $mahost = param("mahost");
                } else { 
                        die("Illegal characters in measurement archive host url.");
                }
        } else {
                $mahost = $Default_mahost;
        }

        # start time
        if (defined(param("stime"))) {
                if (param("stime") =~ m/^[0-9a-zA-Z: \/]+$/) {
                        $stime = param("stime");
                        $epoch_stime = UnixDate(ParseDate($stime),"%s");
                } else {
                        die('Illegal start time: ' . param('stime'));
                }
        } else {
                # default to last 24 hours
                #$epoch_stime = UnixDate(ParseDate("now"),"%s") - 86400;
                #$stime = ParseDateString("epoch $epoch_stime");
                $stime = "yesterday";
                $epoch_stime = UnixDate(ParseDate($stime),"%s");
        }

        # end time
        if (defined(param("etime"))) {
                if (param("etime") =~ m/^[0-9a-zA-Z: \/]+$/) {
                        $etime = param("etime");
                        $epoch_etime = UnixDate(ParseDate($etime),"%s");
                } else {
                        die("Illegal end time.");
                }
        } else {
                $etime = "now";
                $epoch_etime = UnixDate(ParseDate($etime),"%s");
        }
        
        if ($epoch_stime >= $epoch_etime) { 
                die("Start time $epoch_stime is after end time $epoch_etime.");
        }

        if (defined(param('epselect'))) {
                if (param('epselect') =~ m/[0-9a-z]/ ) {
                        $epselect = param('epselect');
                } else {
                        $epselect = "unselected";
                }
        } else {
		$epselect = "unselected";
	}

        # deduplication checkbox
        if (defined(param('donotdedup'))) {
                if (param('donotdedup') eq 1) {
                        $donotdedup = 1;
                } 
        } else {
                $donotdedup = 0;
        }

}



# given something, return the opposite 
sub lookup($;$) {
        my $thing = shift;
        my $af = shift;
        my $r;

        if (defined($dnscache{$thing})) {
                return $dnscache{$thing};
        }

        if (is_ipv4($thing)) {
                $r = gethostbyaddr(inet_pton(AF_INET,$thing),AF_INET);

        } elsif (is_ipv6($thing)) {
                $r = gethostbyaddr(inet_pton(AF_INET6,$thing),AF_INET6);

        # assume we're given a name, and a preference
        } elsif (defined($af)) {
                my $n = scalar(gethostbyname2($thing,$af));
                if (defined($n)) {
                        $r = inet_ntop($af,$n);
                }
        }

        if (defined($r)) { 
                $dnscache{$thing} = $r;
                return $r;      
        } else {
                return " ";
        }
}


sub displayTrData() {

   # display traceroute data

        my $trdata = GetTracerouteDataFromMA($mahost,$epselect,$epoch_stime,$epoch_etime);

        #print Dumper($trdata);

        my %topology;
        DeduplicateTracerouteDataAnswer($trdata,\%topology,$donotdedup);

      #print "<pre>\n";
        #print Dumper(%topology);
      #print "</pre>\n";

      foreach my $time (sort keys %topology) {
              my $humantime = scalar(localtime($time));
              print "<h3>Topology beginning at $humantime</h3><blockquote>\n";
              print "<table border=1 cellspacing=0 cellpadding=3>\n";
              print "<tr><th>Hop</th><th>Router</th><th>IP</th></tr>\n";
              foreach my $hopnum (sort keys %{$topology{$time}} ) {
                      my $sayecmp=" ";
                      foreach my $router (keys %{$topology{$time}{$hopnum}}) {
                              # detect if this hop has more than router
                              my $name = $router;
                              if (scalar(keys %{$topology{$time}{$hopnum}}) > 1) { $sayecmp = "(<b>ECMP</b>)"; }
                              if (lookup($router) ne ' ') {
                                      $name = lookup($router); 
                              }
                              print "<tr><td>$hopnum $sayecmp</td><td>$name</td><td>$router</td></tr>\n";
                      }
              }
              print "</table></blockquote>";
      }
   
} # end displayTrData()


sub displaySelectBox() {

   my $html3=<<EOM;
   Select endpoints available on  $mahost<br>
   <select name="epselect">
   <option value="unselected">Select one ...
EOM
   print $html3;


   foreach my $id (keys %endpoint) {

      my $srchost;
      my $dsthost;

      # some logic to do dns lookups as needed to make the select field human friendly
      if ($endpoint{$id}{'srctype'} =~ m/ipv[46]/ ) {
              $srchost = lookup($endpoint{$id}{'srcval'}) . ' ('. $endpoint{$id}{'srcval'} . ')' ;

      } else { # we have a hostname, but want the ip
              if ($endpoint{$id}{'dsttype'} eq 'ipv4') {
                      $srchost = $endpoint{$id}{'srcval'} . ' ('. lookup($endpoint{$id}{'srcval'},AF_INET) .') ';
              } elsif ($endpoint{$id}{'dsttype'} eq 'ipv6') {
                      $srchost = $endpoint{$id}{'srcval'} . ' ('. lookup($endpoint{$id}{'srcval'},AF_INET6) .') ';
              }
      }

      if ($endpoint{$id}{'dsttype'} =~ m/ipv[46]/ ) {
              $dsthost = lookup($endpoint{$id}{'dstval'}) . ' ('. $endpoint{$id}{'dstval'} . ')' ;

      } else { # we have a hostname, but want the ip, try to guess v4 or v6
                if ($endpoint{$id}{'srctype'} eq 'ipv4') {
                        $dsthost = $endpoint{$id}{'dstval'} . ' ('. lookup($endpoint{$id}{'dstval'},AF_INET) .') ';
                } elsif ($endpoint{$id}{'srctype'} eq 'ipv6') {
                        $dsthost = $endpoint{$id}{'dstval'} . ' ('. lookup($endpoint{$id}{'dstval'},AF_INET6) .') ';
                }
      }

      # determine if something was already selected or not.
      my $selected=" ";
      if ($id eq $epselect) { $selected="selected=\"selected\""; }
      print "<option value=\"$id\" $selected > $srchost ---->  $dsthost \n";
   }

   # see if the checkbox should be selected
   my $dedupsel = " ";
   if ($donotdedup) { 
      $dedupsel = "checked=\"yes\""; 
   } 

   my $html2=<<EOM;
   </select><br>
   <input type="checkbox" name="donotdedup" value="1" $dedupsel>Do not filter/de-duplicate results &nbsp;
   <input type="submit" value="Submit query">
   </form>

EOM
   print $html2;

} #end displaySelectBox()



sub displayTop() {
      my $ma_size = length($mahost) + 10;

      # print some html
      my $html1 =<<EOM;
      <html>
      <head>
       <title>psTracerouteViewer</title>
       <style type="text/css">\@import url($URLPath/jscalendar/calendar-win2k-1.css);</style>
       <script type="text/javascript" src="$URLPath/jscalendar/calendar.js"></script>
       <script type="text/javascript" src="$URLPath/jscalendar/lang/calendar-en.js"></script>
       <script type="text/javascript" src="$URLPath/jscalendar/calendar-setup.js"></script>
      </head>

      <h2>psTracerouteViewer</h2>

      <form name="query1" method="get" action="$Script">
      Measurement Archive: <input type="text" name="mahost" value="$mahost" size="$ma_size"> <br>

      Start Time: <input type="text" id="stime" name="stime" value="$stime" size="18"> 
      <img src="calendaricon.jpg" id="s_trigger" border=0>
      <script type="text/javascript">
         Calendar.setup({
              inputField     :    "stime",           
              ifFormat       :    "%m/%d/%Y %I:%M %p",
              showsTime      :    true,
              button         :    "s_trigger",       
              step           :    1
         });
      </script><br>


      End Time: &nbsp;<input type="text" id="etime" name="etime" value="$etime" size="18">
      <img src="calendaricon.jpg" id="e_trigger" border=0>
      <script type="text/javascript">
         Calendar.setup({
              inputField     :    "etime",           
              ifFormat       :    "%m/%d/%Y %I:%M %p",
              showsTime      :    true,
              button         :    "e_trigger",        
              step           :    1
         });
      </script>
      <br>

      <input type="submit" value="Query MA">

      <br><br>
      <hr>
EOM
      print $html1;

} #end displayTop();


