#/usr/bin/env bash
# bash command completion for neovim remote.
# Source that file in your bashrc to use it.

_nvr_opts_completions()
{
    local cur prev opts
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    opts=(
        -h
        -cc
        -c
        -d
        -l
        -o
        -O
        -p
        -q
        -s
        -t
        --nostart
        --version
        --serverlist
        --servername
        --remote
        --remote-wait
        --remote-silent
        --remote-wait-silent
        --remote-tab
        --remote-tab-wait
        --remote-tab-silent
        --remote-tab-wait-silent
        --remote-send
        --remote-expr
    )
    case "${prev}" in
        --servername)
            srvlist=$(nvr --serverlist)
            COMPREPLY=( $(compgen -W "${srvlist}" -- "$cur") )
            return 0
            ;;
    esac
    if [[ "$cur" =~ ^- ]]; then
        COMPREPLY=( $(compgen -W "${opts[*]}" -- "$cur") )
        return 0
    fi

    COMPREPLY=()
    return 0
}

complete -o default -F _nvr_opts_completions nvr
