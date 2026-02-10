---
title: Post-Restore Instructions - Ready to Execute
type: note
permalink: guides/post-restore-instructions-ready-to-execute
---

# Post-Restore Instructions - Ready to Execute

## When VM Restore Completes

### Step 1: Verify VM is Back Online
```bash
# Test connectivity
ansible -i ansible/inventory.yml media-vm -m ping

# Check if services are running (should be older containers from backup)
ansible -i ansible/inventory.yml media-vm -m shell -a "docker ps | wc -l"
```

### Step 2: Reapply Git Changes
```bash
# Navigate to project directory
cd /home/kuba/dev/lab/feat

# Verify current git status
git status

# Apply the critical inventory fix
git checkout pre-restore-june18 -- ansible/inventory.yml

# Apply Jellyfin SSO configuration
git checkout pre-restore-june18 -- ansible/files/media-vm/jelly/jellyfin.yml

# Verify the changes look correct
git diff --name-only
```

### Step 3: Test Deployment (Dry Run First)
```bash
# Syntax check first
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml --syntax-check

# Dry run to see what would change
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml --check --diff

# If dry run looks good, deploy for real
ansible-playbook -i ansible/inventory.yml ansible/deploy_docker.yml
```

### Step 4: Verification Checklist
- [ ] **Jellyfin**: Access at https://jellyfin.nobasura.org
- [ ] **Users intact**: Can log in with old accounts
- [ ] **Libraries present**: Media shows up correctly
- [ ] **SSO plugin**: Verify it's installed and configured
- [ ] **Servarr stack**: Radarr, Sonarr, Prowlarr accessible
- [ ] **Download clients**: SABnzbd, NZBGet working

### Step 5: Test SSO Integration
- [ ] **Authentik app**: Verify Jellyfin app still exists in Authentik
- [ ] **OIDC flow**: Test login via SSO button
- [ ] **User mapping**: Check if users sync properly

### Troubleshooting
If any issues:
1. **Check container logs**: `docker logs jellyfin`
2. **Verify inventory**: `ansible -i ansible/inventory.yml all --list-hosts`
3. **Compare configs**: Check if any manual tweaks are needed

### Final Steps
1. **Commit the reapplied changes**
2. **Set up automated backups** (high priority!)
3. **Create VM snapshot** after successful verification

---

*Execute these steps once VM restore completes*