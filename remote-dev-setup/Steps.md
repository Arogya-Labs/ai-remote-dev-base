Setup SSH 
 Copy SSH key for remote-dev into the local machine at and run 
`eval "$(ssh-agent -s)"`

Install zsh and set it as default
```
apt install zsh
chsh -s $(which zsh)
```
  
 Install helix
````
sudo add-apt-repository ppa:maveonair/helix-editor
sudo apt update
sudo apt install helix
```
  

Install Zellij
```
curl https://sh.rustup.rs -sSf | sh
cargo install --locked zellij
```
