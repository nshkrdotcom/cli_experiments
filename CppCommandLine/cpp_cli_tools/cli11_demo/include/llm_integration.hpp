#pragma once

#include <string>
#include <memory>
#include <vector>
#include "config_manager.hpp"

class LLMIntegration {
public:
    explicit LLMIntegration(std::shared_ptr<ConfigManager> config);
    ~LLMIntegration() = default;

    // Core LLM functionality
    std::string query(const std::string& prompt, const std::string& system_prompt = "");
    std::string generate_code(const std::string& description);
    bool validate_code_with_llm(const std::string& code);
    
    // Utility functions
    bool is_available();
    std::string get_model_info();
    
    // Self-replication capabilities
    std::string generate_self_improvement(const std::string& current_functionality);
    std::string suggest_new_features();
    
private:
    std::shared_ptr<ConfigManager> config_;
    
    // Helper methods
    std::string execute_llm_command(const std::vector<std::string>& args);
    std::string escape_for_shell(const std::string& input);
    bool check_llm_installation();
};