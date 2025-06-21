#pragma once

#include <string>
#include <map>
#include <fstream>
#include <iostream>
#include <filesystem>

class ConfigManager {
public:
    ConfigManager();
    ~ConfigManager() = default;

    bool load_config(const std::string& config_path = "");
    bool save_config(const std::string& config_path = "");
    
    void set_value(const std::string& key, const std::string& value);
    std::string get_value(const std::string& key, const std::string& default_value = "") const;
    
    bool get_bool(const std::string& key, bool default_value = false) const;
    int get_int(const std::string& key, int default_value = 0) const;
    
    void set_verbose(bool verbose) { verbose_ = verbose; }
    bool is_verbose() const { return verbose_; }
    
    std::string get_llm_command() const;
    std::string get_default_model() const;
    
    void print_config() const;
    
private:
    std::map<std::string, std::string> config_;
    std::string config_file_;
    bool verbose_;
    
    void create_default_config();
    std::string get_default_config_path() const;
};