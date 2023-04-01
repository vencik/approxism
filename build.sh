#!/bin/sh

# Defaults
enable_ut="yes"     # unit tests enabled
build_tgz="no"      # build source package
build_pkg="no"      # build package


usage() {
    cat <<HERE
Usage: $0 [OPTIONS] [-- buildchain parameters]

OPTIONS:
    -h or --help                Print this usage help and exit
    -u or --enable-ut           Enable unit tests run (default: $enable_ut)
    -U or --disable-ut          Disable unit tests run
    -g or --build-tgz           Build source package
    -G or --no-tgz              Don't build source package
    -p or --build-pkg           Build package
    -P or --no-pkg              Don't build package

NOTE: Long options don't work on Mac OS X (with BSD getopt). Use short versions.

HERE
}


echo_colour() {
    colour="$1"; shift
    case "$colour" in
        black)          colour="0;30";;
        dark_gray)      colour="1;30";;
        red)            colour="0;31";;
        light_red)      colour="1;31";;
        green)          colour="0;32";;
        light_green)    colour="1;32";;
        brown)          colour="0;33";;
        orange)         colour="0;33";;
        yellow)         colour="1;33";;
        blue)           colour="0;34";;
        light_blue)     colour="1;34";;
        purple)         colour="0;35";;
        light_purple)   colour="1;35";;
        cyan)           colour="0;36";;
        light_cyan)     colour="1;36";;
        light_gray)     colour="0;37";;
        white)          colour="1;37";;

        *)  echo "INTERNAL ERROR: unsupported colour '$colour'" >&2
            exit 64
            ;;
    esac

    echo "\033[${colour}m$*\033[0m"
}


set -e

# Parse options
platform=$(uname -s)
if test "$platform" = "Linux"; then
    args=$(
        getopt \
            -n "$0" \
            -o huUgGpP \
            --long help,enable-ut,disable-ut,build-tgx,no-tgz,build-pkg,no-pkg \
            -- "$@" \
        || (echo >&2; usage >&2; exit 1)
    )
elif test "$platform" = "Darwin"; then
    args=$(getopt huUgGpP "$@" || (echo >&2; usage >&2; exit 1))
fi

eval set -- "$args"
while true; do
    case "$1" in
        -h|--help)
            usage; exit 0
            ;;

        -u|--enable-ut)
            enable_ut="yes"; shift
            ;;

        -U|--disable-ut)
            enable_ut="no"; shift
            ;;

        -g|--build-tgz)
            build_tgz="yes"; shift
            ;;

        -G|--no-tgz)
            build_tgz="no"; shift
            ;;

        -p|--build-pkg)
            build_pkg="yes"; shift
            ;;

        -P|--no-pkg)
            build_pkg="no"; shift
            ;;

        --) shift; break
            ;;

        *)  echo "INTERNAL ERROR: unresolved legal option '$1'" >&2
            exit 64
            ;;
    esac
done


# Resolve directories
project_dir=$(realpath "$0" | xargs dirname)
source_dir="$project_dir/src"

# Report
echo_colour yellow "Build platform: $platform"
echo_colour yellow "Source directory: $source_dir"
echo_colour yellow "Unit tests enabled: $enable_ut"
echo_colour yellow "Python source package build: $build_python_tgz"
echo_colour yellow "Python package build: $build_python_pkg"
echo


# Unit testing
if which pytest >/dev/null; then
    echo; echo_colour cyan "Running tests..."
    cd "$project_dir"
    pytest --verbose --color=yes src/unit_test
else
    echo; echo_colour red "WARNING: Skipping tests, pytest not found"
fi


# Source tarball build
if test "$build_tgz" = "yes"; then
    echo; echo_colour cyan "Building source package..."
    cd "$project_dir"
    ./adoc2md.sh README.adoc README.md
    python ./setup.py sdist -d .
fi

# Package build
if test "$build_pkg" = "yes"; then
    echo; echo_colour cyan "Building package..."
    cd "$project_dir"
    pip wheel .
fi


# All done
echo_colour green "
------------------
Built SUCCESSFULLY
------------------
"
