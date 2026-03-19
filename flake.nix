{
  description = "org2tc - convert org-mode clock entries to timeclock format";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;

        pythonWithPackages = python.withPackages (ps: [
          ps.pytest
          ps.pytest-cov
          ps.hypothesis
          ps.coverage
        ]);

        org2tc = pkgs.stdenv.mkDerivation {
          pname = "org2tc";
          version = "0.1.0";
          src = self;
          dontBuild = true;
          installPhase = ''
            mkdir -p $out/bin
            install -m755 org2tc $out/bin/org2tc
            substituteInPlace $out/bin/org2tc \
              --replace-fail "#!/usr/bin/env python" "#!${python.interpreter}"
          '';
        };

        mkCheck = name: script: pkgs.runCommand "check-${name}" {
          nativeBuildInputs = [ pythonWithPackages pkgs.ruff ];
        } ''
          cp -r ${self}/. src
          chmod -R +w src
          cd src
          export HOME=$TMPDIR
          export LC_ALL=C
          ${script}
          touch $out
        '';
      in {
        packages.default = org2tc;

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonWithPackages
            pkgs.ruff
            pkgs.lefthook
          ];
        };

        checks = {
          build = org2tc;

          format = mkCheck "format" ''
            ruff format --check org2tc tests/ scripts/
          '';

          lint = mkCheck "lint" ''
            ruff check org2tc tests/ scripts/
          '';

          tests = mkCheck "tests" ''
            python -m pytest tests/ -x -q
          '';

          coverage = mkCheck "coverage" ''
            coverage erase
            ORG2TC_COVERAGE=1 python -m pytest tests/test_org2tc.py -x -q
            coverage report --include='*org2tc' --fail-under=80 || {
              echo "Coverage below threshold. Run tests locally to see details."
              exit 1
            }
          '';

          fuzz = mkCheck "fuzz" ''
            python -m pytest tests/test_fuzz.py -x -q
          '';
        };
      }
    );
}
