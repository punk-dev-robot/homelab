# Technical Investigations Archive

Detailed technical investigations and bug discoveries from infrastructure development.

## Neo4j HTTPS Protocol Investigation

### Problem Statement
Neo4j browser accessed via HTTPS showed "Database access not available" and forced `bolt+s://` connections, while HTTP access worked perfectly.

### Investigation Process
1. **Initial Observation**: HTTPS access broke browser connectivity
2. **Protocol Analysis**: Examined browser behavior differences HTTP vs HTTPS
3. **Database Connection Testing**: Tested various connection protocols
4. **Documentation Research**: Neo4j protocol requirements investigation

### Root Cause Discovery
**Neo4j browser detects HTTPS access and mandates encrypted Bolt connections.**

### Technical Findings
- **Browser Behavior**: HTTPS access → Forces `bolt+s://` protocol (dropdown locked)
- **Discovery API Limitation**: Always advertises `bolt://` regardless of SSL configuration
- **Dual Connection Types**: HTTP/HTTPS (browser) vs Bolt (database) protocols
- **Protocol Enforcement**: Modern browsers enforce protocol consistency

### Production Configuration Solution
```yaml
# Neo4j - Dual protocol support
environment:
  - NEO4J_server_http_enabled=true
  - NEO4J_server_https_enabled=true
  - NEO4J_server_memory_pagecache_size=1G
  - NEO4J_server_memory_heap_max__size=1G
ports:
  - "7474:7474"  # HTTP
  - "7473:7473"  # HTTPS
  - "7687:7687"  # Bolt
```

### Pragmatic Resolution
- **Admin Interface**: `http://apps.lan:7474/browser/` (internal HTTP - works perfectly)
- **External API**: `https://neo4j.lab.nobasura.org` (HTTPS via Caddy)
- **Authentication**: 1Password integration for both access methods

### Key Lessons Learned
1. **Protocol Complexity**: Database protocol architecture requires different proxy approaches
2. **Browser Security**: Modern browsers enforce HTTPS → secure connection consistency
3. **Pragmatic Solutions**: Sometimes internal HTTP access is the optimal solution

---

## User-Agent Rejection Bug Discovery

### Problem Statement
Ansible's `uri` module uses `User-Agent: ansible-httpget` which *arr applications actively reject.

### Impact Analysis
- **Jellyseerr**: Returns `400 Bad Request`
- **Sonarr/Radarr**: Returns `400 Bad Request`
- **All *arr stack**: Actively filters automation tools

### Investigation Process
1. **Test Failure Pattern**: Consistent 400 errors across *arr services
2. **Manual Testing**: Direct curl vs Ansible uri module comparison
3. **Header Analysis**: Identified User-Agent as the differentiator
4. **Application Behavior**: Discovered *arr stack bot protection

### Root Cause
Web applications have built-in protection against automation tools and bots.

### Solution Implementation
```yaml
# Fixed in tests/common/test_base.yml
headers:
  User-Agent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
```

### Validation Results
Manual curl tests confirmed expected behavior:
- **Direct Access**: 200 status
- **App Login Redirect**: 302/307 status

### Cross-Application Impact
This discovery affected testing for 9 services in the *arr ecosystem, demonstrating the importance of understanding application behavior patterns.

### Key Lessons Learned
1. **Application Security**: Modern web apps actively filter automation
2. **Test Realism**: Tests should mimic real user behavior
3. **User-Agent Matters**: Applications make decisions based on User-Agent
4. **Browser Simulation**: Sometimes necessary for accurate testing

---

## Resend SMTP Integration Discovery

### Problem Statement
Pangolin configuration system lacks environment variable substitution, breaking standard Docker configuration patterns.

### Investigation Process
1. **Initial Approach**: Standard Docker env var injection
2. **Configuration Testing**: Env vars not resolving in config files
3. **Documentation Review**: Pangolin config system limitations
4. **Alternative Solutions**: Ansible templating exploration

### Key Discovery
**Pangolin Limitation**: No environment variable substitution in config files  
**Root Cause**: Config system reads static YAML without variable processing

### Solution Development
**Converted config.yml to Jinja2 template with Ansible processing**

```yaml
# Pangolin config.yml.j2 template
email:
  smtp_host: "smtp.resend.com"
  smtp_port: 587
  smtp_user: "resend"
  smtp_pass: "{{ lookup('community.general.onepassword', 'RESEND_API_KEY', vault='Homelab') }}"
  smtp_secure: false
  no_reply: "no-reply@notify.nobasura.org"

flags:
  require_email_verification: false  # Single-email flow
  disable_signup_without_invite: true  # Security
```

### Implementation Details
- **Template Processing**: Ansible resolves 1Password lookups at runtime
- **Security**: `no_log: true` prevents secret exposure
- **Domain Strategy**: notify.nobasura.org for system emails

### DNS Requirements Discovered
- **SPF Record**: Authorize Resend to send emails
- **DKIM Record**: Email authentication
- **DMARC Record**: Email policy enforcement

### Key Lessons Learned
1. **Application Limitations**: Not all systems support standard Docker patterns
2. **Templating Solutions**: Ansible can bridge configuration gaps
3. **Security Considerations**: Template processing requires careful secret handling
4. **Domain Separation**: Clean separation prevents configuration conflicts

---

## Ansible Linting Violation Analysis

### Problem Statement
159 ansible-lint violations across infrastructure codebase preventing production deployment.

### Violation Categories

#### Phase 1: Basic Formatting (159→62)
- **`yaml[trailing-spaces]`**: All trailing whitespace violations
- **`yaml[new-line-at-end-of-file]`**: Missing newline at EOF
- **Resolution**: Editor automation for consistent formatting

#### Phase 2: Configuration Exclusions (62→~10)
- **Docker Compose Discovery**: Files in `files/` are Docker YAML, not Ansible
- **Proper Exclusions**: ansible-lint should only validate Ansible-specific YAML
- **Resolution**: Corrected ansible-lint scope

#### Phase 3: Convention Compliance (~10→10)
- **Variable Naming**: Role-prefixed variables required
- **Handler Names**: Capitalized for consistency
- **Line Length**: Complex conditionals broken into readable format
- **Resolution**: Applied Ansible best practices

#### Phase 4: Collection Dependencies (10→0)
- **Root Cause**: Missing community collections in ansible-lint environment
- **Resolution**: `ansible-galaxy install -r requirements.yaml --force`

### Critical System Administration Discovery
**❌ NEVER**: `pip install package` on Arch Linux (breaks system packages)  
**✅ ALWAYS**: Use `pipx install package` for Python CLI tools (isolated environments)

### Production Standards Established
1. **No trailing whitespace** in any YAML files
2. **Always end files with newline** character
3. **Role-prefixed variables** prevent naming conflicts
4. **Capitalized handler names** for consistency
5. **FQCN usage** for community collections

### Key Lessons Learned
1. **Incremental Approach**: Systematic violation reduction is more effective
2. **Tool Understanding**: ansible-lint requires proper collection setup
3. **System Package Management**: Arch Linux requires careful Python tool management
4. **Production Standards**: Consistent formatting and naming conventions matter

---

## Investigation Summary

### Technical Discoveries
- **Neo4j Protocol Complexity**: Browser HTTPS enforcement affects database connections
- **Application Bot Protection**: Modern web apps actively filter automation tools
- **Configuration System Limitations**: Not all applications support standard Docker patterns
- **Linting Environment Setup**: Tool dependencies must be properly configured

### Solution Patterns
- **Dual Access Methods**: Internal HTTP + External HTTPS for different use cases
- **Browser Simulation**: User-Agent manipulation for realistic testing
- **Template-Based Configuration**: Ansible templating bridges application limitations
- **Incremental Problem Solving**: Systematic approach to complex issues

### Impact on Architecture
- **Pragmatic Solutions**: Balance between ideal and practical implementation
- **Security Considerations**: Multiple authentication patterns for different access methods
- **Testing Requirements**: Realistic test conditions mirror actual usage
- **Production Standards**: Automated enforcement of code quality standards

## Related Notes
- [Completed Tasks History](../archive/completed-tasks-history.md) - Related task completions
- [Troubleshooting Guide](../reference/troubleshooting-guide.md) - Debugging procedures
- [Implementation Details Archive](../archive/implementation-details-archive.md) - Detailed patterns