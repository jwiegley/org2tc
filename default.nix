{ pkgs ? import <nixpkgs> {}
}:

pkgs.stdenv.mkDerivation {
  name = "org2tc";
  buildInputs = [ pkgs.python3 ];
  src = ./.;
  unpackPhase = "";
  installPhase = ''
    mkdir -p $out/bin
    cp ${./org2tc} $out/bin/org2tc
    chmod +x $out/bin/org2tc
  '';
}
