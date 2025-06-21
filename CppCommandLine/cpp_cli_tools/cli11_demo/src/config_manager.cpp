#include "config_manager.hpp"
#include <sstream>
#include <algorithm>

ConfigManager::ConfigManager() : verbose_(false) {
    config_file_ = get_default_config_path();
    if (!load_config()) {
        create_default_config();
    }
}

bool ConfigManager::load_config(const std::string& config_path) {
    std::string path = config_path.empty() ? config_file_ : config_path;
    
    if (!std::filesystem::exists(path)) {
        if (verbose_) {
            std::cout << "Config file not found: " << path << std::endl;
        }
        return false;
    }
    
    std::ifstream file(path);
    if (!file.is_open()) {
        if (verbose_) {
            std::cout << "Failed to open config file: " << path << std::endl;
        }
        return false;
    }
    
    config_.clear();
    std::string line;
    
    while (std::getline(file, line)) {
        // Skip comments and empty lines
        if (line.empty() || line[0] == '#') continue;
        
        // Find the delimiter
        size_t pos = line.find('=');
        if (pos != std::string::npos) {
            std::string key = line.substr(0, pos);
            std::string value = line.substr(pos + 1);
            
            // Trim whitespace
            key.erase(0, key.find_first_not_of(" \t"));
            key.erase(key.find_last_not_of(" \t") + 1);
            value.erase(0, value.find_first_not_of(" \t"));
            value.erase(value.find_last_not_of(" \t") + 1);
            
            config_[key] = value;
        }
    }
    
    config_file_ = path;
    if (verbose_) {
        std::cout << "Config loaded from: " << path << std::endl;
    }
    return true;
}

bool ConfigManager::save_config(const std::string& config_path) {
    std::string path = config_path.empty() ? config_file_ : config_path;
    
    std::ofstream file(path);
    if (!file.is_open()) {
        if (verbose_) {
            std::cout << "Failed to save config file: " << path << std::endl;
        }
        return false;
    }
    
    file << "# Self-Evolving CLI Tool Configuration\n";
    file << "# Generated automatically\n\n";
    
    for (const auto& [key, value] : config_) {
        file << key << " = " << value << "\n";
    }
    
    if (verbose_) {
        std::cout << "Config saved to: " << path << std::endl;
    }
    return true;
}

void ConfigManager::set_value(const std::string& key, const std::string& value) {
    config_[key] = value;
}

std::string ConfigManager::get_value(const std::string& key, const std::string& default_value) const {
    auto it = config_.find(key);
    return (it != config_.end()) ? it->second : default_value;
}

bool ConfigManager::get_bool(const std::string& key, bool default_value) const {
    std::string value = get_value(key);
    if (value.empty()) return default_value;
    
    std::transform(value.begin(), value.end(), value.begin(), ::tolower);
    return (value == "true" || value == "1" || value == "yes" || value == "on");
}

int ConfigManager::get_int(const std::string& key, int default_value) const {
    std::string value = get_value(key);
    if (value.empty()) return default_value;
    
    try {
        return std::stoi(value);
    } catch (const std::exception&) {
        return default_value;
    }
}

std::string ConfigManager::get_llm_command() const {
    return get_value("llm.command", "llm");
}

std::string ConfigManager::get_default_model() const {
    return get_value("llm.model", "gpt-3.5-turbo");
}

void ConfigManager::print_config() const {
    std::cout << "Configuration Settings:\n";
    std::cout << "=====================\n";
    for (const auto& [key, value] : config_) {
        std::cout << key << " = " << value << "\n";
    }
    std::cout << "\nConfig file: " << config_file_ << "\n";
}

void ConfigManager::create_default_config() {
    config_["version"] = "1.0.0";
    config_["verbose"] = "false";
    config_["llm.command"] = "llm";
    config_["llm.model"] = "gpt-3.5-turbo";
    config_["llm.temperature"] = "0.7";
    config_["llm.max_tokens"] = "2000";
    config_["llm.timeout"] = "30";
    config_["execution.safe_mode"] = "true";
    config_["execution.max_time"] = "60";
    config_["validation.enabled"] = "true";
    config_["history.max_entries"] = "1000";
    config_["paths.generated_dir"] = "generated";
    config_["paths.history_dir"] = "history";
    
    save_config();
}

std::string ConfigManager::get_default_config_path() const {
    const char* home = std::getenv("HOME");
    if (home) {
        return std::string(home) + "/.cli_evolve_config";
    }
    return "cli_evolve_config.txt";
}