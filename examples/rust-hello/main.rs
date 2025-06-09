use std::env;

fn main() {
    // Get hostname
    let hostname = gethostname::gethostname()
        .to_string_lossy()
        .to_string();
    println!("Hello from {}!", hostname);
    
    // Get OS and architecture
    println!("Running on {}/{}", env::consts::OS, env::consts::ARCH);
    
    // Get Rust version (compile-time)
    println!("Built with Rust {}", env!("CARGO_PKG_RUST_VERSION"));
} 