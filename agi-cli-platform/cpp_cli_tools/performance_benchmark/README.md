# Performance Benchmark Suite

Comparative benchmarks demonstrating C++ performance advantages for CLI tools.

## Benchmarks

1. **String Processing** - Large string manipulation operations
2. **Mathematical Computation** - Intensive numerical calculations  
3. **Memory Management** - Allocation and deallocation patterns
4. **File I/O** - Reading and writing large files
5. **System Calls** - Direct OS interaction performance

## Results

Run `make benchmark` to see performance comparisons between:
- C++ (optimized)
- Python equivalent
- Memory usage analysis
- Startup time comparison

## Building

```bash
mkdir build && cd build
cmake ..
make
./benchmark_suite
```