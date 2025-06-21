#include "command_executor.hpp"
#include "llm_integration.hpp"
#include <iostream>
#include <fstream>
#include <chrono>
#include <random>
#include <thread>
#include <filesystem>
#include <iomanip>
#include <vector>
#include <cmath>

CommandExecutor::CommandExecutor(std::shared_ptr<ConfigManager> config) 
    : config_(config) {
}

bool CommandExecutor::evolve_command(const std::string& description, bool execute, bool save) {
    std::cout << "Evolving: " << description << std::endl;
    
    // Generate code using LLM
    LLMIntegration llm(config_);
    std::string generated_code = llm.generate_code(description);
    
    if (generated_code.empty() || generated_code == "LLM command not available") {
        std::cout << "Failed to generate code" << std::endl;
        return false;
    }
    
    std::cout << "Code generated successfully" << std::endl;
    std::cout << "Generated code preview:\n" << generated_code.substr(0, 200) << "..." << std::endl;
    
    if (execute || save) {
        // Validate generated code
        if (!validate_code(generated_code)) {
            std::cout << "Generated code failed validation" << std::endl;
            return false;
        }
        
        std::string command_id = generate_command_id();
        
        if (save) {
            // Save permanently
            if (save_generated_command(command_id, generated_code)) {
                std::cout << "Command saved with ID: " << command_id << std::endl;
            }
        }
        
        if (execute) {
            // For demonstration, we'll just show what would be executed
            std::cout << "Command execution simulation completed" << std::endl;
            log_command(description, "Success");
        }
    }
    
    return true;
}

bool CommandExecutor::execute_system_command(const std::string& command) {
    if (config_->get_bool("execution.safe_mode", true)) {
        std::cout << "Safe mode enabled. Would execute: " << command << std::endl;
        return true;
    }
    
    std::cout << "Executing: " << command << std::endl;
    int result = system(command.c_str());
    return result == 0;
}

bool CommandExecutor::query_llm(const std::string& query) {
    std::cout << "Querying LLM: " << query << std::endl;
    
    LLMIntegration llm(config_);
    std::string response = llm.query(query);
    
    if (!response.empty() && response != "LLM command not available") {
        std::cout << "Response:\n" << std::string(20, '-') << "\n";
        std::cout << response << std::endl;
        return true;
    } else {
        std::cout << "No response from LLM" << std::endl;
        return false;
    }
}

void CommandExecutor::show_status() {
    std::cout << "AGI CLI Platform Status\n";
    std::cout << std::string(40, '=') << "\n";
    std::cout << "Version: " << config_->get_value("version", "unknown") << "\n";
    std::cout << "Config file: " << config_->get_value("config_file", "default") << "\n";
    LLMIntegration llm(config_);
    std::cout << "LLM available: " << (llm.is_available() ? "Yes" : "No") << "\n";
    std::cout << "LLM command: " << config_->get_llm_command() << "\n";
    std::cout << "Default model: " << config_->get_default_model() << "\n";
    std::cout << "Safe mode: " << (config_->get_bool("execution.safe_mode", true) ? "Enabled" : "Disabled") << "\n";
    
    // Show available commands count
    auto history = load_command_history();
    std::cout << "Command history: " << history.size() << " entries\n";
}

void CommandExecutor::show_history() {
    auto history = load_command_history();
    
    if (history.empty()) {
        std::cout << "No command history found" << std::endl;
        return;
    }
    
    std::cout << "Command History\n";
    std::cout << std::string(40, '=') << "\n";
    
    // Show last 10 entries
    size_t start = history.size() > 10 ? history.size() - 10 : 0;
    for (size_t i = start; i < history.size(); ++i) {
        std::cout << "Entry " << (i + 1) << ": " << history[i] << "\n";
        std::cout << std::string(20, '-') << "\n";
    }
}

void CommandExecutor::show_version() {
    std::cout << "AGI CLI Platform v" << config_->get_value("version", "1.0.0") << "\n";
    std::cout << "Built with CLI11 and modern C++17\n";
    std::cout << "Self-evolving intelligence framework for AGI development\n";
}

bool CommandExecutor::validate_code(const std::string& code) {
    if (!config_->get_bool("validation.enabled", true)) {
        std::cout << "Code validation is disabled" << std::endl;
        return true;
    }
    
    // Basic validation checks
    if (code.empty()) {
        std::cout << "Code validation failed: empty code" << std::endl;
        return false;
    }
    
    if (code.length() > 50000) {
        std::cout << "Code validation failed: code too long" << std::endl;
        return false;
    }
    
    // Check for dangerous patterns
    std::vector<std::string> dangerous_patterns = {
        "system(", "exec(", "rm -rf", "format C:", "delete *"
    };
    
    for (const auto& pattern : dangerous_patterns) {
        if (code.find(pattern) != std::string::npos) {
            std::cout << "Code validation failed: dangerous pattern detected: " << pattern << std::endl;
            return false;
        }
    }
    
    // Use LLM for additional validation if available
    LLMIntegration llm(config_);
    if (llm.is_available()) {
        bool llm_result = llm.validate_code_with_llm(code);
        if (!llm_result) {
            std::cout << "Code validation failed: LLM validation" << std::endl;
            return false;
        }
    }
    
    std::cout << "Code validation passed" << std::endl;
    return true;
}

std::string CommandExecutor::generate_command_id() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(10000000, 99999999);
    return std::to_string(dis(gen));
}

void CommandExecutor::benchmark_performance() {
    std::cout << "Performance Benchmark\n";
    std::cout << std::string(40, '=') << "\n";
    
    // Test 1: String operations
    auto start = std::chrono::high_resolution_clock::now();
    std::string result;
    for (int i = 0; i < 100000; ++i) {
        result += "test_string_" + std::to_string(i);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "String operations (100k): " << duration.count() << " microseconds\n";
    
    // Test 2: Mathematical operations
    start = std::chrono::high_resolution_clock::now();
    double sum = 0.0;
    for (int i = 0; i < 1000000; ++i) {
        sum += std::sqrt(i) * std::sin(i);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "Math operations (1M): " << duration.count() << " microseconds\n";
    std::cout << "Result sum: " << std::fixed << std::setprecision(2) << sum << "\n";
    
    // Test 3: Memory allocation
    start = std::chrono::high_resolution_clock::now();
    std::vector<std::vector<int>> vectors;
    for (int i = 0; i < 10000; ++i) {
        vectors.emplace_back(100, i);
    }
    end = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "Memory allocation (10k vectors): " << duration.count() << " microseconds\n";
}

void CommandExecutor::demonstrate_cpp_advantages() {
    std::cout << "C++ Advantages Demonstration\n";
    std::cout << std::string(40, '=') << "\n";
    
    std::cout << "1. Compile-time optimizations: Templates and constexpr\n";
    std::cout << "2. Zero-cost abstractions: RAII, smart pointers\n";
    std::cout << "3. Direct memory management: Stack vs heap control\n";
    std::cout << "4. System-level access: Direct OS API calls\n";
    std::cout << "5. Performance: Native code execution\n";
    std::cout << "6. Type safety: Compile-time error detection\n";
    std::cout << "7. Cross-platform: Single codebase, multiple targets\n";
    
    benchmark_performance();
}

bool CommandExecutor::save_generated_command(const std::string& id, const std::string& code) {
    std::string generated_dir = config_->get_value("paths.generated_dir", "generated");
    
    // Create directory if it doesn't exist
    if (!std::filesystem::exists(generated_dir)) {
        std::filesystem::create_directories(generated_dir);
    }
    
    std::string filename = generated_dir + "/command_" + id + ".cpp";
    std::ofstream file(filename);
    
    if (!file.is_open()) {
        std::cout << "Failed to save command to: " << filename << std::endl;
        return false;
    }
    
    file << "// Generated command ID: " << id << "\n";
    file << "// Generated at: " << std::chrono::system_clock::now().time_since_epoch().count() << "\n\n";
    file << code;
    
    log_command("Save command " + id, "Success: " + filename);
    return true;
}

std::vector<std::string> CommandExecutor::load_command_history() {
    std::vector<std::string> history;
    std::string history_dir = config_->get_value("paths.history_dir", "history");
    std::string history_file = history_dir + "/commands.log";
    
    if (!std::filesystem::exists(history_file)) {
        return history;
    }
    
    std::ifstream file(history_file);
    std::string line;
    
    while (std::getline(file, line)) {
        if (!line.empty()) {
            history.push_back(line);
        }
    }
    
    return history;
}

void CommandExecutor::log_command(const std::string& description, const std::string& result) {
    std::string history_dir = config_->get_value("paths.history_dir", "history");
    
    // Create directory if it doesn't exist
    if (!std::filesystem::exists(history_dir)) {
        std::filesystem::create_directories(history_dir);
    }
    
    std::string history_file = history_dir + "/commands.log";
    std::ofstream file(history_file, std::ios::app);
    
    if (file.is_open()) {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        
        file << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
        file << " | " << description << " | " << result << "\n";
    }
}