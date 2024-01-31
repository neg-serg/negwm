{
  description = "Application packaged using poetry2nix";
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication mkPoetryPackages;
        propagatedBuildInputs = [ pkgs.python3.xlib ];
      in
      {
        packages = {
          negwm = mkPoetryApplication { projectDir = self; };
          negwm_pkg = mkPoetryPackages { projectDir = ./.; };
          default = self.packages.${system}.negwm;
        };
        

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.negwm ];
          packages = [ pkgs.poetry ];
        };
      });
}
