#pragma once

#include <string>
#include <vector>
#include <memory>
#include "config_manager.hpp"

class CommandExecutor {
public:
    explicit CommandExecutor(std::shared_ptr<ConfigManager> config);
    ~CommandExecutor() = default;

    // Core functionality
    bool evolve_command(const std::string& description, bool execute = false, bool save = false);
    bool execute_system_command(const std::string& command);
    bool query_llm(const std::string& query);
    
    // Information commands
    void show_status();
    void show_history();
    void show_version();
    
    // Utility functions
    bool validate_code(const std::string& code);
    std::string generate_command_id();
    
    // Performance demonstration
    void benchmark_performance();
    void demonstrate_cpp_advantages();
    
private:
    std::shared_ptr<ConfigManager> config_;
    
    // Helper methods
    bool save_generated_command(const std::string& id, const std::string& code);
    std::vector<std::string> load_command_history();
    void log_command(const std::string& description, const std::string& result);
};