Setup SSH 
 Copy SSH key for remote-dev into the local machine at (make it permission 400) and run 
```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_arogya_remote_dev
```


Install zsh and set it as default
```
apt install zsh
chsh -s $(which zsh)
```
  
 Install helix

```
sudo add-apt-repository ppa:maveonair/helix-editor
sudo apt update
sudo apt install helix
```
  
Install Zellij
```
curl https://sh.rustup.rs -sSf | sh
cargo install --locked zellij
```
Optionals
* glow for tui markdown renderer
```
 snap install glow
```
