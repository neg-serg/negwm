#!/bin/sh

xdg_config_home_check() {
    if [ -z "$XDG_CONFIG_HOME" ]; then
        echo "\$XDG_CONFIG_HOME should be set to install"
        exit 1
    fi

    if [ -d "$XDG_CONFIG_HOME/negi3wm" ]; then
        echo "create backup of current i3 config directory..."
        mv -v "$XDG_CONFIG_HOME/negi3wm" "$XDG_CONFIG_HOME/negi3wm_backup_$(date --rfc-3339=seconds|tr ' ' '-')"
    fi
}

pip_deps_install() {
    echo "install python dependencies..."
    sudo pip install -r "$XDG_CONFIG_HOME/negi3wm/requirements.txt" --upgrade
}

git_clone() {
    if ! which git > /dev/null; then
        echo "Install git"
        sudo pacman -S git --noconfirm
    fi
    git clone https://github.com/neg-serg/negi3wm "$XDG_CONFIG_HOME/negi3wm"
}

install_yay() {
    if ! which yay > /dev/null; then
        echo "Installing yay"
        git clone https://aur.archlinux.org/yay.git "/tmp/yay"
        cd "/tmp/yay"
        makepkg -si --noconfirm
    fi
}

install_python_deps() {
    echo "checking for pip3 installed..."
    if which pip3 > /dev/null; then
        pip_deps_install
    else
        echo "trying to install python-pip..."
        if which yay > /dev/null; then
            yay -S python-pip --noconfirm
        else
            echo "Currently only Arch linux is supported with yay installer"
            exit 1
        fi
        if [ ! -z $?  ]; then
            echo "install failed :("
            exit 1
        fi
        pip_deps_install
    fi
}

install_mandatory_deps() {
    install_deps i3 dash
}

install_recommended_deps() {
    install_deps zsh tmux rofi dunst xdo alacritty pulseaudio
}

install_deps() {
    for dep in "$@"; do
        echo -n "Check for $dep..."
        if ! which "$dep" > /dev/null; then
            echo "Install $dep..."
            yay -S "$dep" --noconfirm || yay -S "$dep-git" --noconfirm
        else
            echo " $dep is already installed [OK]"
        fi
    done
}

main(){
    xdg_config_home_check
    git_clone
    install_yay
    install_python_deps
    install_mandatory_deps
    install_recommended_deps
}

main "$@"
