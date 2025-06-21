#include "CLI/CLI.hpp"
#include <iostream>
#include <memory>
#include "config_manager.hpp"
#include "command_executor.hpp"

int main(int argc, char** argv) {
    // Initialize configuration
    auto config = std::make_shared<ConfigManager>();
    CommandExecutor executor(config);
    
    // Create the main CLI app
    CLI::App app{"AGI CLI Platform - Self-evolving intelligence framework for AGI development"};
    
    // Global options
    bool verbose = false;
    std::string config_file;
    
    app.add_flag("-v,--verbose", verbose, "Enable verbose output");
    app.add_option("-c,--config", config_file, "Configuration file path");
    
    // Set verbose mode
    if (verbose) {
        config->set_verbose(true);
        config->set_value("verbose", "true");
    }
    
    // Load custom config if specified
    if (!config_file.empty()) {
        config->load_config(config_file);
    }
    
    // Evolve command - core functionality
    auto evolve_cmd = app.add_subcommand("evolve", "Generate and integrate new functionality using LLM");
    std::string description;
    bool execute = false;
    bool save = false;
    
    evolve_cmd->add_option("description", description, "Description of functionality to generate")->required();
    evolve_cmd->add_flag("-e,--execute", execute, "Execute the generated command immediately");
    evolve_cmd->add_flag("-s,--save", save, "Save the generated command permanently");
    
    evolve_cmd->callback([&]() {
        if (!executor.evolve_command(description, execute, save)) {
            std::cerr << "Evolution failed" << std::endl;
            return;
        }
    });
    
    // Status command
    auto status_cmd = app.add_subcommand("status", "Show current tool status and configuration");
    status_cmd->callback([&]() {
        executor.show_status();
    });
    
    // History command
    auto history_cmd = app.add_subcommand("history", "Show command generation history");
    history_cmd->callback([&]() {
        executor.show_history();
    });
    
    // LLM query command
    auto llm_cmd = app.add_subcommand("query", "Direct LLM query for experimentation");
    std::string query;
    llm_cmd->add_option("query", query, "Query to send to LLM")->required();
    llm_cmd->callback([&]() {
        if (!executor.query_llm(query)) {
            std::cerr << "LLM query failed" << std::endl;
        }
    });
    
    // Version command
    auto version_cmd = app.add_subcommand("version", "Show version information");
    version_cmd->callback([&]() {
        executor.show_version();
    });
    
    // Config command
    auto config_cmd = app.add_subcommand("config", "Configuration management");
    
    auto config_show = config_cmd->add_subcommand("show", "Show current configuration");
    config_show->callback([&]() {
        config->print_config();
    });
    
    auto config_set = config_cmd->add_subcommand("set", "Set configuration value");
    std::string key, value;
    config_set->add_option("key", key, "Configuration key")->required();
    config_set->add_option("value", value, "Configuration value")->required();
    config_set->callback([&]() {
        config->set_value(key, value);
        config->save_config();
        std::cout << "Set " << key << " = " << value << std::endl;
    });
    
    // Benchmark command - showcase C++ advantages
    auto benchmark_cmd = app.add_subcommand("benchmark", "Run performance benchmarks");
    benchmark_cmd->callback([&]() {
        executor.benchmark_performance();
    });
    
    // Demo command - demonstrate C++ advantages
    auto demo_cmd = app.add_subcommand("demo", "Demonstrate C++ advantages for CLI tools");
    demo_cmd->callback([&]() {
        executor.demonstrate_cpp_advantages();
    });
    
    // System command - execute system commands safely
    auto system_cmd = app.add_subcommand("exec", "Execute system commands (safe mode)");
    std::string command;
    system_cmd->add_option("command", command, "Command to execute")->required();
    system_cmd->callback([&]() {
        if (!executor.execute_system_command(command)) {
            std::cerr << "Command execution failed" << std::endl;
        }
    });
    
    // Self-improve command - use LLM for self-improvement suggestions
    auto improve_cmd = app.add_subcommand("improve", "Generate self-improvement suggestions");
    improve_cmd->callback([&]() {
        std::string current_features = R"(
Current CLI tool features:
- LLM integration for code generation
- Command evolution and execution
- Configuration management
- Performance benchmarking
- Safe code validation
- Command history tracking
)";
        
        if (!executor.query_llm("Suggest improvements for this CLI tool: " + current_features)) {
            std::cerr << "Self-improvement query failed" << std::endl;
        }
    });
    
    // Default behavior - show help if no command
    if (argc == 1) {
        std::cout << app.help() << std::endl;
        return 0;
    }
    
    // Parse and execute
    try {
        app.parse(argc, argv);
    } catch (const CLI::ParseError &e) {
        return app.exit(e);
    }
    
    return 0;
}