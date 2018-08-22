#!/bin/bash
set -e
SCRIPT_PATH=$(realpath $0)
DIR_PATH=$(dirname $SCRIPT_PATH)


add_fossasia_repo() {
    echo "Set pip repo for root"
    if ! sudo test -d /root/.pip; then sudo mkdir /root/.pip; fi
    echo -e "[global]\nextra-index-url=https://repo.fury.io/fossasia/" | sudo tee /root/.pip/pip.conf
    echo "Set pip repo for current user"
    if [ ! -d ~/.config/pip ]; then mkdir -p ~/.config/pip ; fi
    echo -e "[global]\nextra-index-url=https://repo.fury.io/fossasia/" > ~/.config/pip/pip.conf
}

add_debian_repo() {
    echo "Add ReSpeaker Debian repo"
    # Respeaker driver https://github.com/respeaker/deb
    wget -qO- http://respeaker.io/deb/public.key | sudo apt-key add -
    echo "deb http://respeaker.io/deb/ stretch main" | sudo tee /etc/apt/sources.list.d/respeaker.list
    sudo apt update
}

install_debian_dependencies()
{
    sudo -E apt install -y python3-pip sox libsox-fmt-all flac \
    python3-cairo python3-flask mpv flite ca-certificates-java pixz udisks2
    # We specify ca-certificates-java instead of openjdk-(8/9)-jre-headless, so that it will pull the
    # appropriate version of JRE-headless, which can be 8 or 9, depending on ARM6 or ARM7 platform.
}

function install_seed_voicecard_driver()
{
    echo "installing Respeaker Mic Array drivers from source"
    git clone https://github.com/respeaker/seeed-voicecard.git
    cd seeed-voicecard
    sudo ./install.sh
    cd ..
    tar czf ~/seeed-voicecard.tar.gz seeed-voicecard
    rm -rf seeed-voicecard
}

function install_dependencies()
{
    install_seed_voicecard_driver
}

function susi_server(){
    if  [ ! -d "susi_server" ]
    then
        mkdir $DIR_PATH/susi_server
        cd $DIR_PATH/susi_server
        git clone --recurse-submodules https://github.com/fossasia/susi_server.git
        git clone https://github.com/fossasia/susi_skill_data.git
        # The .git folder is big. Delete it (we don't do susi_server deveplopment here, so no need to keep it)
        rm -rf susi_server/.git
    fi

    if [ -d "susi_server" ]
    then
        echo "Deploying local server"
        cd $DIR_PATH/susi_server/susi_server
        {
            ./gradlew build
        } || {
            echo PASS
        }

        bin/start.sh
    fi
}

####  Main  ####
add_fossasia_repo
add_debian_repo

echo "Downloading dependency: Susi Python API Wrapper"
if [ ! -d "susi_python" ]
then
    git clone https://github.com/fossasia/susi_api_wrapper.git

    echo "setting correct location"
    mv susi_api_wrapper/python_wrapper/susi_python susi_python
    mv susi_api_wrapper/python_wrapper/requirements.txt requirements.txt
    rm -rf susi_api_wrapper
fi

echo "Installing required Debian Packages"
install_debian_dependencies

echo "Installing Python Dependencies"
sudo -H pip3 install -U pip wheel
sudo -H pip3 install -r requirements.txt  # This is from susi_api_wrapper
sudo -H pip3 install -r requirements-hw.txt
sudo -H pip3 install -r requirements-special.txt

echo "Downloading Speech Data for flite TTS"

if [ ! -f "extras/cmu_us_slt.flitevox" ]
then
    wget "http://www.festvox.org/flite/packed/flite-2.0/voices/cmu_us_slt.flitevox" -P extras
fi

echo
echo "NOTE: Snowboy is not compatible with all systems. If the setup indicates failed, use PocketSphinx engine for Hotword"
echo

echo "Updating the Udev Rules"
cd $DIR_PATH
sudo ./media_daemon/media_udev_rule.sh

echo "Cloning and building SUSI server"
susi_server

echo "Updating Systemd Rules"
sudo bash $DIR_PATH/Deploy/auto_boot.sh

echo "Creating a backup folder for future factory_reset"
sudo tar -Ipixz -cf ../reset_folder.tar.xz susi_linux
mv ../reset_folder.tar.xz $DIR_PATH/factory_reset/reset_folder.tar.xz

echo "Converting RasPi into an Access Point"
sudo bash $DIR_PATH/access_point/wap.sh

echo -e "\033[0;92mSUSI is installed successfully!\033[0m"
echo -e "Run configuration script by 'python3 config_generator.py \033[0;32m<stt engine> \033[0;33m<tts engine> \033[0;34m<snowboy or pocketsphinx> \033[0;35m<wake button?>' \033[0m"
echo "For example, to configure SUSI as following: "
echo -e "\t \033[0;32m-Google for speech-to-text"
echo -e "\t \033[0;33m-Google for text-to-speech"
echo -e "\t \033[0;34m-Use snowboy for hot-word detection"
echo -e "\t \033[0;35m-Do not use GPIO for wake button\033[0m"
echo -e "python3 config_generator.py \033[0;32mgoogle \033[0;33mgoogle \033[0;34my \033[0;35mn \033[0m"
