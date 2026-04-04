add_executable(fit)
target_link_libraries(fit PUBLIC yaml-cpp::yaml-cpp ROOT::Core ROOT::Hist ROOT::Graf ROOT::Gui ROOT::Tree ROOT::RooFit ROOT::ROOTDataFrame)
target_sources(fit PRIVATE fit.cxx)