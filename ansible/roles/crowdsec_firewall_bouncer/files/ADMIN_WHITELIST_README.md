# CrowdSec Admin IP Whitelist Configuration

## Current Whitelisted IPs
- **`<ADMIN_HOME_IP>`** - User home IP (CRITICAL - DO NOT REMOVE, sourced from 1Password ADMIN_IP_CONFIG)
- **10.100.0.0/16** - Pangolin tunnel network
- **172.16.0.0/12** - Docker internal networks
- **127.0.0.1** - Localhost
- **::1** - IPv6 localhost

## Adding New Admin IPs

To add new admin IPs (office, mobile, backup locations), edit these files:

1. **Primary Whitelist Parser** (recommended):
   `/config/crowdsec/parsers/s02-enrich/custom-admin-whitelist.yaml`
   - Add IPs to the `ip:` list
   - Add networks to the `cidr:` list

2. **Profile Protection** (additional safety):
   `/config/crowdsec/profiles.yaml`
   - Update the filter condition in `whitelist_admin_ips` profile

3. **Scenario Protection** (extra safety):
   `/config/crowdsec/scenarios/custom-whitelist-protection.yaml`
   - Update the filter to exclude new IPs

## Best Practices

1. **Always test** after adding new IPs:
   ```bash
   # Try to manually ban the IP
   docker exec crowdsec cscli decisions add --ip YOUR_IP --duration 1m
   # Check if it was added (it should be if whitelist works)
   docker exec crowdsec cscli decisions list | grep YOUR_IP
   # Remove test ban
   docker exec crowdsec cscli decisions delete --ip YOUR_IP
   ```

2. **Keep multiple admin IPs** whitelisted:
   - Home IP
   - Office IP  
   - Mobile/hotspot IP
   - VPN exit IP

3. **Document changes** with comments in the YAML files

4. **Regular review** - Remove old IPs that are no longer needed

## Emergency Access

If you get locked out:
1. Use the VPS console access (Oracle Cloud Console)
2. Disable CrowdSec temporarily: `docker stop crowdsec`
3. Fix whitelist configuration
4. Restart CrowdSec: `docker start crowdsec`