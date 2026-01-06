from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Count, Q
from .models import UserData, SubmitProof, RedeemedReward
from math import radians, sin, cos, sqrt, atan2

#  Haversine distance
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = radians(lat2 - lat1)
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

#  UserData Admin
@admin.register(UserData)
class UserDataAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'earned_coins', 'spent_coins', 'coins_left', 'rank')
    readonly_fields = ('earned_coins', 'spent_coins', 'rank')

# SubmitProof Admin 
@admin.register(SubmitProof)
class SubmitProofAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'activity_type', 'submission_date', 'status',
        'claimed_latitude', 'claimed_longitude',
        'exif_latitude', 'exif_longitude',
        'live_latitude', 'live_longitude',
        'proof_preview', 'calculated_distance_display', 'views_actions'
    )
    readonly_fields = (
        'claimed_latitude', 'claimed_longitude',
        'exif_latitude', 'exif_longitude',
        'live_latitude', 'live_longitude',
        'calculated_distance', 'earned_coins'
    )
    list_filter = ('activity_type', 'status')
    search_fields = ('user__name', 'activity_type')

    # Proof image preview
    def proof_preview(self, obj):
        if obj.proof_image:
            return format_html('<img src="{}" width="100" height="100" />', obj.proof_image.url)
        return "No Image"
    proof_preview.short_description = 'Proof Image'

    # Display calculated distance 
    def calculated_distance_display(self, obj):
        if obj.calculated_distance is not None:
            return f"{int(obj.calculated_distance)} m"
        return "N/A"
    calculated_distance_display.short_description = "Distance"

    # Approve/Reject buttons
    def views_actions(self, obj):
        return format_html(
            '<a class="button" href="approve/{}/"> Accept</a>&nbsp;'
            '<a class="button" href="reject/{}/"> Reject</a>',
            obj.pk, obj.pk
        )
    views_actions.short_description = 'Actions'

    # Custom URLs for approve/reject
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:proof_id>/', self.admin_site.admin_view(self.approve_proof), name='approve-proof'),
            path('reject/<int:proof_id>/', self.admin_site.admin_view(self.reject_proof), name='reject-proof'),
        ]
        return custom_urls + urls

    # Update leaderboard
    def update_leaderboard(self):
        users = UserData.objects.annotate(
            solar_panel_count=Count(
                'submitproof', filter=Q(submitproof__activity_type='Solar Panel Installation')
            ),
            tree_plantation_count=Count(
                'submitproof', filter=Q(submitproof__activity_type='Tree Plantation')
            ),
            total_submissions=Count('submitproof')
        ).order_by(
            '-earned_coins',
            '-total_submissions',
            '-solar_panel_count',
            '-tree_plantation_count',
            'id'
        )
        rank = 1
        for user in users:
            user.rank = rank
            user.save()
            rank += 1

    # Approve proof (admin)
    def approve_proof(self, request, proof_id):
        proof = SubmitProof.objects.get(pk=proof_id)
       
        if proof.calculated_distance is None:
            try:
                if proof.exif_latitude is not None and proof.exif_longitude is not None:
                    if proof.claimed_latitude is not None and proof.claimed_longitude is not None:
                        proof.calculated_distance = calculate_distance(
                            proof.claimed_latitude, proof.claimed_longitude,
                            proof.exif_latitude, proof.exif_longitude
                        )
                    elif proof.live_latitude is not None and proof.live_longitude is not None:
                        proof.calculated_distance = calculate_distance(
                            proof.live_latitude, proof.live_longitude,
                            proof.exif_latitude, proof.exif_longitude
                        )
            except Exception as e:
                print("Distance calculation error:", e)
                proof.calculated_distance = None

        proof.status = 'Accepted'
        proof.save()
        self.update_leaderboard()
        messages.success(request, f"Proof by {proof.user.name} accepted.")
        return redirect(request.META.get('HTTP_REFERER'))

    # Reject proof
    def reject_proof(self, request, proof_id):
        proof = SubmitProof.objects.get(pk=proof_id)
        proof.status = 'Rejected'
        proof.save()
        messages.warning(request, f"Proof by {proof.user.name} rejected.")
        return redirect(request.META.get('HTTP_REFERER'))

#  RedeemedReward Admin 
@admin.register(RedeemedReward)
class RedeemedRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward_name', 'cost', 'redeemed_at')
    search_fields = ('user__name', 'reward_name')
    list_filter = ('redeemed_at',)
