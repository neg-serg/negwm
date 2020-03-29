#!/bin/sh

xdg_config_home_check() {
    if [ -z "$XDG_CONFIG_HOME" ]; then
        echo "\$XDG_CONFIG_HOME should be set to install"
    fi

    if [ -d "$XDG_CONFIG_HOME/i3" ]; then
        echo "create backup of current i3 config directory..."
        mv -v "$XDG_CONFIG_HOME/i3"{,_bck}
    fi
}

pip_deps_install() {
    echo -n "[ok]"
    echo "install python dependencies..."
    sudo pip install -r ./requirements.txt --upgrade
}

git_clone() {
    if ! which git > /dev/null; then
        echo "Install git"
        sudo pacman -S git --noconfirm
    fi
    git clone git@github.com:neg-serg/negi3wm "$XDG_CONFIG_HOME/i3"
}

change_dir() {
    cd $XDG_CONFIG_HOME/i3
    echo "current dir is: $(pwd)"
}

install::yay() {
    if ! which yay > /dev/null; then
        echo "Installing yay"
        git clone https://aur.archlinux.org/yay.git "/tmp/yay"
        cd "/tmp/yay"
        makepkg -si --noconfirm
    fi
}

install::python_deps() {
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

install::mandatory_deps() {
    install::deps i3 ppi3 dash
}

install::recommended_deps() {
    install::deps zsh tmux rofi dunst xdo alacritty pulseaudio
}

install::deps() {
    for dep in "$@"; do
        echo -n "Check for $dep..."
        if ! which "$dep" > /dev/null; then
            echo "Install $dep..."
            yay -S "$dep" --noconfirm || yay -S "$dep-git" --noconfirm
        else
            echo -n " $dep is already installed [OK]"
        fi
    done
}

# 'xrescat': 'extract xresources for theming',
main(){
    xdg_config_home_check
    git_clone
    change_dir
    install::yay
    install::python_deps
    install::mandatory_deps
    install::recommended_deps
}

main "$@"
