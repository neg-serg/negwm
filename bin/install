#!/usr/bin/env dash

negwm_dir_prepare() {
    if [ -z "$XDG_CONFIG_HOME" ]; then
        echo "\$XDG_CONFIG_HOME should be set to install"
        exit 1
    fi

    if [ -d "$XDG_CONFIG_HOME/negwm" ]; then
        echo "create backup of current i3 config directory..."
        mv -v "$XDG_CONFIG_HOME/negwm" "$XDG_CONFIG_HOME/negwm_backup_$(date --rfc-3339=seconds|tr ' ' '-')"
    fi
}

git_clone() {
    if ! which git > /dev/null; then
        echo "Install git"
        sudo pacman -S git --noconfirm
    fi
    git clone https://github.com/neg-serg/negwm "$XDG_CONFIG_HOME/negwm"
}

pip_deps_install() {
    echo "install python dependencies..."
    sudo pip install -r "$XDG_CONFIG_HOME/negwm/requirements.txt" --upgrade
}

install_python_deps() {
    if which pip3 > /dev/null; then
        pip_deps_install
    else
        echo 'you need pip to install negwm'
    fi
}

main(){
    negwm_dir_prepare
    git_clone
    install_python_deps
}

main "$@"
