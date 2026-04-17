from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Backfill Django user is_staff/is_superuser flags from supabase_role column'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not persist changes')
        parser.add_argument('--roles', nargs='+', default=['superuser', 'admin', 'superadmin'], help='Roles to promote')

    def handle(self, *args, **options):
        User = get_user_model()
        dry_run = options['dry_run']
        roles = [r.lower() for r in options['roles']]

        qs = User.objects.filter(supabase_role__in=roles)
        total = qs.count()
        self.stdout.write(f'Found {total} users with supabase_role in {roles}')

        promoted = 0
        for user in qs:
            try:
                role_val = (user.supabase_role or '').lower()
                if role_val in roles:
                    if not user.is_staff or not user.is_superuser:
                        self.stdout.write(f'Promoting {user.username} ({role_val})')
                        promoted += 1
                        if not dry_run:
                            user.is_staff = True
                            user.is_superuser = True
                            user.save(update_fields=['is_staff', 'is_superuser'])
            except Exception as e:
                logger.exception('Failed processing user %s: %s', getattr(user, 'username', '<unknown>'), e)

        self.stdout.write(f'Promoted {promoted} users (dry_run={dry_run})')
