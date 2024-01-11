%global scons_ver 4.5.2
%global scons python3 scons-%{scons_ver}/scripts/scons.py
%global note1 The Red Hat support for this package is limited. See
%global note2 https://access.redhat.com/support/policy/gpsd-support for more details.

Name:           gpsd-minimal
Version:        3.25
Release:        4%{?dist}
Epoch:          1
Summary:        Service daemon for mediating access to a GPS

License:        BSD
URL:            https://gpsd.gitlab.io/gpsd/index.html
Source0:        https://download-mirror.savannah.gnu.org/releases/gpsd/gpsd-%{version}.tar.gz
# used only for building
Source1:        https://github.com/SCons/scons/archive/%{scons_ver}/scons-%{scons_ver}.tar.gz
Source11:       gpsd.sysconfig

# add missing IPv6 support
Patch1:         gpsd-ipv6.patch
# fix some issues reported by coverity and shellcheck
Patch2:         gpsd-scanfixes.patch
# fix busy wait when reading from gpsd socket
Patch3:         gpsd-busywait.patch

BuildRequires:  gcc
BuildRequires:  dbus-devel
BuildRequires:  ncurses-devel
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pyserial
BuildRequires:  bluez-libs-devel
BuildRequires:  pps-tools-devel
BuildRequires:  systemd-rpm-macros
BuildRequires:  libusb1-devel

Requires:       udev
%{?systemd_requires}

Conflicts:      gpsd < %{epoch}:%{version}-%{release}

%description
gpsd is a service daemon that mediates access to a GPS sensor
connected to the host computer by serial or USB interface, making its
data on the location/course/velocity of the sensor available to be
queried on TCP port 2947 of the host computer.

%{note1}
%{note2}

%package clients
Summary:        Clients for gpsd
Requires:       python3-pyserial
Conflicts:      gpsd-clients < %{epoch}:%{version}-%{release}

%description clients
This package contains various clients using gpsd.

%{note1}
%{note2}

%prep
%setup -q -n gpsd-%{version} -a 1
%patch -P 1 -p1 -b .ipv6
%patch -P 2 -p1 -b .scanfixes
%patch -P 3 -p1 -b .busywait

# add note to man pages about limited support
sed -i ':a;$!{N;ba};s|\(\.SH "[^"]*"\)|.SH "NOTE"\n%{note1}\n%{note2}\n\1|3' \
    man/*.{1,8}

# add path to the private python gps module
sed -i 's|\( *\)\(import gps\)$|\1sys.path.insert(1, "%{_libdir}/gpsd%{version}")\n\1\2|' \
    *.py.in clients/*.py.in

# don't try reloading systemd when installing in the build root
sed -i 's|systemctl daemon-reload|true|' SConscript

iconv -f iso8859-1 -t utf8 NEWS > NEWS_ && mv NEWS_ NEWS

%build
export CCFLAGS="%{optflags}"
# scons ignores LDFLAGS. LINKFLAGS partially work (some flags like
# -spec=... are filtered)
export LINKFLAGS="%{__global_ldflags}"

# breaks with %%{_smp_mflags}
%{scons} \
    dbus_export=yes \
    systemd=yes \
    qt=no \
    xgps=no \
    debug=yes \
    leapfetch=no \
    manbuild=no \
    prefix="" \
    sysconfdif=%{_sysconfdir} \
    bindir=%{_bindir} \
    includedir=%{_includedir} \
    libdir=%{_libdir}/gpsd%{version} \
    sbindir=%{_sbindir} \
    mandir=%{_mandir} \
    mibdir=%{_docdir}/gpsd \
    docdir=%{_docdir}/gpsd \
    pkgconfigdir=%{_libdir}/pkgconfig \
    icondir=%{_datadir}/gpsd \
    udevdir=$(dirname %{_udevrulesdir}) \
    unitdir=%{_unitdir} \
    target_python=python3 \
    python_shebang=%{python3} \
    python_libdir=%{_libdir}/gpsd%{version} \
    build

%install
# avoid rebuilding
export CCFLAGS="%{optflags}"
export LINKFLAGS="%{__global_ldflags}"

DESTDIR=%{buildroot} %{scons} install systemd_install udev-install

# use the old name for udev rules
mv %{buildroot}%{_udevrulesdir}/{25,99}-gpsd.rules

install -d -m 0755 %{buildroot}%{_sysconfdir}/sysconfig
install -p -m 0644 %{SOURCE11} \
    %{buildroot}%{_sysconfdir}/sysconfig/gpsd

# Missed in scons install
install -p -m 0755 gpsinit %{buildroot}%{_sbindir}

# Remove shebang and fix permissions
sed -i '/^#!.*python/d' %{buildroot}%{_libdir}/gpsd%{version}/gps/{aio,}gps.py
chmod 644 %{buildroot}%{_libdir}/gpsd%{version}/gps/gps.py

# Remove unpackaged files
rm -f %{buildroot}%{_libdir}/gpsd%{version}/lib{gps*.so,gps.so.*}
rm -f %{buildroot}%{_libdir}/gpsd%{version}/*.egg-info
rm -rf %{buildroot}%{_libdir}/gpsd%{version}/pkgconfig
rm -rf %{buildroot}%{_includedir}
rm -rf %{buildroot}%{_mandir}/man{3,5}
rm -r %{buildroot}%{_mandir}/man1/xgps*
rm -rf %{buildroot}%{_datadir}/gpsd

rm -rf %{buildroot}%{_docdir}/gpsd

%post
%systemd_post gpsd.service gpsd.socket

%preun
%systemd_preun gpsd.service gpsd.socket

%postun
# Don't restart the service
%systemd_postun gpsd.service gpsd.socket

%files
%doc README.adoc NEWS
%license COPYING
%config(noreplace) %{_sysconfdir}/sysconfig/gpsd
%{_sbindir}/gpsd
%{_sbindir}/gpsdctl
%{_sbindir}/gpsinit
%{_bindir}/gpsmon
%{_bindir}/gpsctl
%{_bindir}/ntpshmmon
%{_bindir}/ppscheck
%{_unitdir}/gpsd.service
%{_unitdir}/gpsd.socket
%{_unitdir}/gpsdctl@.service
%{_udevrulesdir}/*.rules
%{_mandir}/man8/gpsd.8*
%{_mandir}/man8/gpsdctl.8*
%{_mandir}/man8/gpsinit.8*
%{_mandir}/man8/ppscheck.8*
%{_mandir}/man1/gpsmon.1*
%{_mandir}/man1/gpsctl.1*
%{_mandir}/man1/ntpshmmon.1*

%files clients
%license COPYING
%{_libdir}/gpsd%{version}/libgpsdpacket.so.*
%{_libdir}/gpsd%{version}/gps
%{_bindir}/cgps
%{_bindir}/gegps
%{_bindir}/gps2udp
%{_bindir}/gpscat
%{_bindir}/gpscsv
%{_bindir}/gpsdebuginfo
%{_bindir}/gpsdecode
%{_bindir}/gpspipe
%{_bindir}/gpsplot
%{_bindir}/gpsprof
%{_bindir}/gpsrinex
%{_bindir}/gpssnmp
%{_bindir}/gpssubframe
%{_bindir}/gpxlogger
%{_bindir}/lcdgps
%{_bindir}/gpsfake
%{_bindir}/ubxtool
%{_bindir}/zerk
%{_mandir}/man1/gegps.1*
%{_mandir}/man1/gps.1*
%{_mandir}/man1/gps2udp.1*
%{_mandir}/man1/gpscsv.1*
%{_mandir}/man1/gpsdebuginfo.1*
%{_mandir}/man1/gpsdecode.1*
%{_mandir}/man1/gpspipe.1*
%{_mandir}/man1/gpsplot.1*
%{_mandir}/man1/gpsprof.1*
%{_mandir}/man1/gpsrinex.1*
%{_mandir}/man1/gpssnmp.1*
%{_mandir}/man1/gpssubframe.1*
%{_mandir}/man1/gpxlogger.1*
%{_mandir}/man1/lcdgps.1*
%{_mandir}/man1/cgps.1*
%{_mandir}/man1/gpscat.1*
%{_mandir}/man1/gpsfake.1*
%{_mandir}/man1/ubxtool.1*
%{_mandir}/man1/zerk.1*

%changelog
* Tue Aug 08 2023 Miroslav Lichvar <mlichvar@redhat.com> - 1:3.25-4
- fix busy wait when reading from gpsd socket

* Tue Aug 08 2023 Miroslav Lichvar <mlichvar@redhat.com> - 1:3.25-3
- fix gpsfake to load python gps module

* Tue Aug 01 2023 Miroslav Lichvar <mlichvar@redhat.com> - 1:3.25-2
- add missing IPv6 support
- fix some issues reported by coverity and shellcheck

* Mon Jul 24 2023 Miroslav Lichvar <mlichvar@redhat.com> - 1:3.25-1
- initial release based on Fedora gpsd package
