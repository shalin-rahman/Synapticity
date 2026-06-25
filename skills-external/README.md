# External Skills Directory

This directory contains custom or external skills that Synapticity will load alongside the local `skills/` directory.

## Structure

Each skill should be organized as:
```
skills-external/
├── skill-name-1/
│   └── skill.md
├── skill-name-2/
│   └── skill.md
└── ...
```

## Priority

- **External skills override local skills** if they have the same name
- Skills are injected dynamically based on keywords and task context
- The SkillRegistry automatically discovers and loads skills from this directory on startup

## Adding New External Skills

1. Create a folder with your skill name (use hyphens for multi-word names)
2. Add a `skill.md` file with your skill content
3. Restart Synapticity or enable hot-reload to load the new skill

Example:
```
skills-external/
└── custom-fastapi-patterns/
    └── skill.md
```

## Hot-Reload Support

With `ENABLE_HOT_RELOAD: True` in config.py, changes to skill files are automatically detected and reloaded without restarting.

## More Information

See [synaptic/core/skill_registry.py](../synaptic/core/skill_registry.py) for the implementation details.
