const nextConfig = {
  // 'standalone' produces a minimal self-contained output for Docker.
  // The compose dev target skips the build step entirely, so this only
  // affects the prod image.
  output: 'standalone',
}

export default nextConfig
