{ pkgs }:
{
  deps = [
    pkgs.python310
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.nodejs_20
  ];
}
