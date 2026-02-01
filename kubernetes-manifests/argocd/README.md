# ArgoCD GitOps Configuration for GenovaAI

This directory contains the ArgoCD configuration for GitOps-based continuous deployment of the GenovaAI DNA Analysis Platform.

## Overview

ArgoCD is a declarative GitOps continuous delivery tool for Kubernetes. It automatically syncs your cluster state with the desired state defined in Git.

## Directory Structure

```
argocd/
├── argocd.yaml                 # Core ArgoCD components (namespace, deployments, services, RBAC)
├── argocd-application.yaml     # GenovaAI Application CRD definition
├── argocd-image-updater.yaml   # Automatic image update controller
├── kustomization.yaml          # Kustomize configuration for ArgoCD
└── README.md                   # This file
```

## Deployment Options

### Option 1: Deploy with Kustomize (Recommended)

```bash
# Deploy all ArgoCD components at once
kubectl apply -k kubernetes-manifests/argocd/
```

### Option 2: Deploy Individually

```bash
# Step 1: Deploy ArgoCD core components
kubectl apply -f kubernetes-manifests/argocd/argocd.yaml

# Step 2: Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Step 3: Deploy Image Updater (optional)
kubectl apply -f kubernetes-manifests/argocd/argocd-image-updater.yaml

# Step 4: Deploy GenovaAI Application
kubectl apply -f kubernetes-manifests/argocd/argocd-application.yaml
```

### Option 3: Run Without ArgoCD (Traditional)

You can still deploy GenovaAI without ArgoCD using the main kubernetes-manifests:

```bash
# Deploy GenovaAI directly
kubectl apply -k kubernetes-manifests/
```

## Accessing ArgoCD UI

### Port Forward (Development)

```bash
# Forward ArgoCD server to localhost
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Access at: https://localhost:8080
```

### Get Initial Admin Password

```bash
# Get the auto-generated admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Login with:
# Username: admin
# Password: <output from above command>
```

### Change Admin Password

```bash
# Using ArgoCD CLI
argocd login localhost:8080 --insecure
argocd account update-password
```

## Image Updater Configuration

The Image Updater automatically updates container images when new versions are pushed to the registry.

### Supported Update Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `latest` | Always use `:latest` tag | Development |
| `semver` | Follow semantic versioning | Production |
| `digest` | Track image digests | Immutable deployments |
| `name` | Alphabetically sorted tags | Custom versioning |

### Configure for GenovaAI

Edit `argocd-application.yaml` annotations:

```yaml
annotations:
  # Track latest tag (development)
  argocd-image-updater.argoproj.io/genovaai.update-strategy: latest
  
  # Or track semver (production)
  argocd-image-updater.argoproj.io/genovaai.update-strategy: semver
  argocd-image-updater.argoproj.io/genovaai.allow-tags: regexp:^v[0-9]+\.[0-9]+\.[0-9]+$
```

### Private Registry Authentication

For private Docker Hub repositories, create a secret:

```bash
kubectl create secret docker-registry dockerhub-secret \
  -n argocd \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<token>
```

Then uncomment the pull-secret annotation in `argocd-application.yaml`.

## Sync Policies

### Automated Sync

The GenovaAI application is configured with automated sync:

- **Prune**: Removes resources that no longer exist in Git
- **Self-Heal**: Reverts manual changes made directly to the cluster
- **Retry**: Automatically retries failed syncs up to 5 times

### Manual Sync

To temporarily disable auto-sync and sync manually:

```bash
# Disable auto-sync
argocd app set genovaai --sync-policy none

# Manual sync
argocd app sync genovaai

# Re-enable auto-sync
argocd app set genovaai --sync-policy automated
```

## Monitoring

### Check Application Status

```bash
# Using kubectl
kubectl get applications -n argocd

# Using ArgoCD CLI
argocd app list
argocd app get genovaai
```

### View Sync Status

```bash
# Check sync status
argocd app get genovaai --show-operation

# View sync history
argocd app history genovaai
```

### Image Updater Logs

```bash
# Check image updater logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-image-updater -f
```

## Troubleshooting

### Application Stuck in "Progressing"

```bash
# Check application events
kubectl describe application genovaai -n argocd

# Force refresh
argocd app get genovaai --hard-refresh
```

### Sync Failed

```bash
# Get detailed sync status
argocd app sync genovaai --dry-run

# Check for resource conflicts
kubectl get events -n genovaai --sort-by='.lastTimestamp'
```

### Image Updater Not Working

```bash
# Check if image updater is running
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-image-updater

# View logs
kubectl logs -n argocd deployment/argocd-image-updater

# Verify application annotations
kubectl get application genovaai -n argocd -o yaml | grep -A 20 annotations
```

## Best Practices

1. **Separate Branches**: Use different branches for dev/staging/prod
2. **Sealed Secrets**: Use Sealed Secrets or external secret managers for sensitive data
3. **Resource Limits**: Always define resource limits in manifests
4. **Health Checks**: Ensure all deployments have proper health probes
5. **Sync Waves**: Use sync waves for complex deployments with dependencies

## Related Documentation

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Image Updater](https://argocd-image-updater.readthedocs.io/)
- [Kustomize Documentation](https://kustomize.io/)
- [GenovaAI Kubernetes Manifests](../README.md)
