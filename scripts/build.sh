#!/usr/bin/env bash
# TODO: Cleanup the file into functions?


# >> Utils

log() {
    # Source: https://github.com/kisslinux/kiss/blob/master/kiss#L16
    # Print a message prettily.
    #
    # All messages are printed to stderr to allow the user to hide build
    # output which is the only thing printed to stdout.
    #
    # '\033[1;32m'        Set text to color '2' and make it bold.
    # '\033[m':           Reset text formatting.
    # '${3:-->}':         If the 3rd argument is missing, set prefix to '->'.
    # '${2:+\033[1;3Xm}': If the 2nd argument exists, set text style of '$1'.
    # '${2:+\033[m}':     If the 2nd argument exists, reset text formatting.
    printf '\033[1;33m%s \033[m%b%s\033[m %s\n' \
           "${3:-->}" "${2:+\033[1;36m}" "$1" "$2" >&2
}

usage() {
    cat << USAGE
Usage: build.sh [OPTIONS]

When no options are provided, builds the docker images for the project normally

Options:
    --clean       Clean up the build cruft then exit

    -h, --help    Prints this help message
USAGE
}



# >> Test if docker desktop experimental features is installed

[ -n "$(docker buildx 2>&1 | grep 'not a docker command')" ] && {
    log "prerequisites" "Experimental Docker Desktop features not enabled"
    exit 1
}



# >> Command line input

builder_name="builder-quadsbot"

while [ "$1" != "" ]; do
    case $1 in
        --clean )     log "cleanup" "Removeing builder $builder_name"
                      docker buildx rm $builder_name
                      exit
                      ;;
        -h | --help ) usage
                      exit
                      ;;
        * )           log "arg_parsing" "Invalid argument: $1"
                      exit
    esac
done



# >> Setup docker builder


[ -z "$(docker buildx ls | grep "$builder_name")" ] && {
    log "setup_build_env" "Builder does not exist"

    log "setup_build_env" "Creating builder: $builder_name"
    docker buildx create --name $builder_name

    log "setup_build_env" "Use and setup $builder_name"
    docker buildx use $builder_name
    docker buildx inspect --bootstrap
}



# >> Build quadsbot docker image

log "quadsbot" "Build quadsbot image"
docker buildx build --platform linux/arm/v6 -t akeboshiwind/quadsbot:latest -f Dockerfile.armv6 --push .
