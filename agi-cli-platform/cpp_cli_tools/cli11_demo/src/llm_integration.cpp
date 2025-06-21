#include "llm_integration.hpp"
#include <iostream>
#include <sstream>
#include <array>
#include <memory>
#include <cstdlib>
#include <algorithm>
#include <vector>

LLMIntegration::LLMIntegration(std::shared_ptr<ConfigManager> config) 
    : config_(config) {
    if (!check_llm_installation()) {
        std::cerr << "Warning: 'llm' command not found. Please install it for full functionality.\n";
    }
}

std::string LLMIntegration::query(const std::string& prompt, const std::string& system_prompt) {
    if (!is_available()) {
        return "LLM command not available";
    }
    
    std::vector<std::string> args;
    args.push_back(config_->get_llm_command());
    
    // Add model if specified
    std::string model = config_->get_default_model();
    if (!model.empty()) {
        args.push_back("-m");
        args.push_back(model);
    }
    
    // Add system prompt if provided
    if (!system_prompt.empty()) {
        args.push_back("-s");
        args.push_back(system_prompt);
    }
    
    // Add the main prompt
    args.push_back(prompt);
    
    return execute_llm_command(args);
}

std::string LLMIntegration::generate_code(const std::string& description) {
    std::string system_prompt = R"(You are a C++ code generator for a self-evolving CLI tool.
Generate clean, safe, and functional C++ code based on the user's description.
The code should be compatible with CLI11 and follow these guidelines:

1. Use modern C++17 features
2. Include proper error handling
3. Add comments and documentation
4. Return complete, compilable code
5. Use CLI11 patterns for command-line parsing
6. Follow C++ best practices

Return ONLY the C++ code without any explanations or markdown formatting.)";

    std::string user_prompt = "Generate C++ code for: " + description + 
                             "\n\nThe code should be a complete function or class that can be integrated into a CLI11-based application.";
    
    return query(user_prompt, system_prompt);
}

bool LLMIntegration::validate_code_with_llm(const std::string& code) {
    std::string system_prompt = R"(You are a C++ code validator for a self-evolving CLI tool.
Analyze the provided C++ code and respond with only 'SAFE' or 'UNSAFE'.

Check for:
1. Dangerous system calls or operations
2. Memory safety issues
3. Potential security vulnerabilities
4. Resource leaks
5. Code injection risks

Respond with only 'SAFE' if the code is acceptable, or 'UNSAFE' if it poses any security risks.)";

    std::string user_prompt = "Validate this C++ code:\n\n```cpp\n" + code + "\n```";
    
    std::string response = query(user_prompt, system_prompt);
    
    // Convert to uppercase for comparison
    std::transform(response.begin(), response.end(), response.begin(), ::toupper);
    
    return response.find("SAFE") != std::string::npos;
}

bool LLMIntegration::is_available() {
    return check_llm_installation();
}

std::string LLMIntegration::get_model_info() {
    if (!is_available()) {
        return "LLM not available";
    }
    
    std::vector<std::string> args = {config_->get_llm_command(), "--version"};
    return execute_llm_command(args);
}

std::string LLMIntegration::generate_self_improvement(const std::string& current_functionality) {
    std::string prompt = "Given this current CLI tool functionality: " + current_functionality + 
                        "\n\nSuggest specific improvements or new features that would make this tool more capable of self-evolution and AGI development.";
    
    return query(prompt);
}

std::string LLMIntegration::suggest_new_features() {
    std::string prompt = R"(Suggest new features for a self-evolving C++ CLI tool that can:
1. Generate and execute new commands using LLM
2. Modify its own functionality
3. Serve as a foundation for AGI development

Focus on practical, implementable features that showcase C++ advantages over Python.)";
    
    return query(prompt);
}

std::string LLMIntegration::execute_llm_command(const std::vector<std::string>& args) {
    if (args.empty()) return "";
    
    // Build command string
    std::ostringstream cmd_stream;
    for (size_t i = 0; i < args.size(); ++i) {
        if (i > 0) cmd_stream << " ";
        cmd_stream << escape_for_shell(args[i]);
    }
    
    std::string command = cmd_stream.str();
    if (config_->is_verbose()) {
        std::cout << "Executing: " << command << std::endl;
    }
    
    // Execute command and capture output
    std::array<char, 128> buffer;
    std::string result;
    
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(command.c_str(), "r"), pclose);
    if (!pipe) {
        return "Failed to execute LLM command";
    }
    
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }
    
    // Remove trailing newline if present
    if (!result.empty() && result.back() == '\n') {
        result.pop_back();
    }
    
    return result;
}

std::string LLMIntegration::escape_for_shell(const std::string& input) {
    std::string escaped = "'";
    for (char c : input) {
        if (c == '\'') {
            escaped += "'\\''";
        } else {
            escaped += c;
        }
    }
    escaped += "'";
    return escaped;
}

bool LLMIntegration::check_llm_installation() {
    std::string command = "which " + config_->get_llm_command() + " > /dev/null 2>&1";
    return system(command.c_str()) == 0;
}