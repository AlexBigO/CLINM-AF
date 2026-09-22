# How to use Geant4 projects?

1. Go into a project folder. For instance,
```
cd BeamOnTarget
```

2. Prepare the compilation tools using CMake:
```
cmake -S . -B build
```

3. Compile (make) and store the compilation output in `build` folder:
```
cmake --build build -j4
```