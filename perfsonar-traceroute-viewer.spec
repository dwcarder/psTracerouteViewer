%define web_base /usr/lib/perfsonar/traceroute-viewer
%define lib_base /usr/lib/perfsonar/lib

# cron/apache entries are located in the 'etc' directory
%define apacheconf apache-perfsonar-traceroute-viewer.conf 

%define perfsonar_auto_version 5.0.0
%define perfsonar_auto_relnum 0.a1.0

Name:			perfsonar-traceroute-viewer
Version:		%{perfsonar_auto_version}
Release:		%{perfsonar_auto_relnum}%{?dist}
Summary:		perfSONAR Traceroute Viewer
License:		Distributable, see LICENSE
Group:			Development/Libraries
URL:			http://www.perfsonar.net
Source0:		perfsonar-traceroute-viewer-%{version}.%{perfsonar_auto_relnum}.tar.gz
BuildRoot:		%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:		noarch
Requires:		perl
Requires:		perl(CGI)
Requires:		perl(CGI::Carp)
Requires:		perl(Data::Dumper)
Requires:		perl(Data::Validate::IP)
Requires:		perl(Date::Manip)
Requires:		perl(DateTime::TimeZone)
Requires:		perl(Exporter)
Requires:		perl(POSIX)
Requires:		perl(Socket)
Requires:		perl(Socket6)
Requires:		httpd
Requires:		libperfsonar-esmond-perl
Obsoletes:		perl-perfSONAR_PS-Toolkit

%description
The perfSONAR Traceroute Viewer (psTracerouteViewer) is a library and cgi for viewing 
traceroute data stored in perfSONAR.

%pre
/usr/sbin/groupadd -r -r perfsonar 2> /dev/null || :
/usr/sbin/useradd -g perfsonar -r -s /sbin/nologin -c "perfSONAR User" -d /tmp perfsonar 2> /dev/null || :

%prep
%setup -q -n perfsonar-traceroute-viewer-%{version}.%{perfsonar_auto_relnum}

%build

%install
rm -rf %{buildroot}

mkdir -p %{buildroot}/%{web_base}
mkdir -p %{buildroot}/%{lib_base}
mkdir -p %{buildroot}/etc/httpd/conf.d

install -D -m 0755 index.cgi %{buildroot}/%{web_base}
install -D -m 0644 uwm.gif %{buildroot}/%{web_base}
install -D -m 0644 calendaricon.jpg %{buildroot}/%{web_base}
cp -r jscalendar %{buildroot}/%{web_base}/jscalendar

install -D -m 0755 psTracerouteUtils.pm %{buildroot}/%{lib_base}

install -D -m 0644 %{apacheconf} %{buildroot}/etc/httpd/conf.d/%{apacheconf}

%clean
rm -rf %{buildroot}

%post

%files
%defattr(-,perfsonar,perfsonar,-)
%{web_base}/*
%attr(0755,perfsonar,perfsonar) %{web_base}/index.cgi
%{lib_base}/*
/etc/httpd/conf.d/%{apacheconf}

%changelog
* Tue Feb 9 2016 andy@es.net 3.5.1-0.0.a1
- Initial RPM
