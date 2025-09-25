import logging
from flask import render_template, request, redirect, url_for, session, flash
from . import bp
from .. import db
from ..utils import login_required, instructor_required, SESSION_USER_ID

@bp.route('/create', methods=['GET', 'POST'])
@instructor_required
def create_organization():
    user_id = session[SESSION_USER_ID]

    # Check if user is already in an organization
    user_profile_ref = db.collection('player_profiles').document(user_id)
    user_profile = user_profile_ref.get()
    if user_profile.exists and user_profile.to_dict().get('organization_id'):
        flash("You are already a member of an organization.", "info")
        return redirect(url_for('organization.dashboard'))

    if request.method == 'POST':
        org_name = request.form.get('name', '').strip()
        if not org_name:
            flash("Organization name is required.", "error")
            return render_template('organization/create_organization.html')

        try:
            # Create the organization
            org_ref = db.collection('organizations').document()
            org_ref.set({
                'name': org_name,
                'instructors': [user_id],
                'members': [user_id]
            })

            # Update the user's profile
            user_profile_ref.update({'organization_id': org_ref.id})

            flash(f"Organization '{org_name}' created successfully!", "success")
            return redirect(url_for('organization.dashboard'))
        except Exception as e:
            logging.error(f"Error creating organization for user {user_id}: {e}")
            flash("An error occurred while creating the organization.", "error")

    return render_template('organization/create_organization.html')

@bp.route('/dashboard')
@instructor_required
def dashboard():
    user_id = session[SESSION_USER_ID]
    user_profile = db.collection('player_profiles').document(user_id).get()
    if not user_profile.exists:
        flash("Your user profile could not be found.", "error")
        return redirect(url_for('profile.profile'))

    org_id = user_profile.to_dict().get('organization_id')
    if not org_id:
        return redirect(url_for('organization.create_organization'))

    try:
        org_doc = db.collection('organizations').document(org_id).get()
        if not org_doc.exists:
            flash("Your organization could not be found.", "error")
            # Clear the invalid org id from the user's profile
            db.collection('player_profiles').document(user_id).update({'organization_id': db.DELETE_FIELD})
            return redirect(url_for('profile.profile'))

        organization = org_doc.to_dict()

        # Fetch member details
        member_profiles = []
        member_ids = organization.get('members', [])
        for member_id in member_ids:
            profile = db.collection('player_profiles').document(member_id).get()
            if profile.exists:
                member_profiles.append(profile.to_dict())

        return render_template('organization/dashboard.html', organization=organization, members=member_profiles)
    except Exception as e:
        logging.error(f"Error loading organization dashboard for user {user_id}: {e}")
        flash("An error occurred while loading the organization dashboard.", "error")
        return redirect(url_for('profile.profile'))

import uuid

@bp.route('/invite', methods=['GET', 'POST'])
@instructor_required
def invite():
    user_id = session[SESSION_USER_ID]
    user_profile = db.collection('player_profiles').document(user_id).get()
    org_id = user_profile.to_dict().get('organization_id')

    if not org_id:
        flash("You must be in an organization to invite users.", "warning")
        return redirect(url_for('profile.profile'))

    if request.method == 'POST':
        role = request.form.get('role', 'student')
        invite_code = str(uuid.uuid4())

        try:
            db.collection('invites').document(invite_code).set({
                'organization_id': org_id,
                'role': role,
                'created_by': user_id
            })
            flash(f"Invite code generated: {invite_code}", "success")
        except Exception as e:
            logging.error(f"Error creating invite code for org {org_id}: {e}")
            flash("Failed to create invite code.", "error")

        return redirect(url_for('organization.dashboard'))

    return render_template('organization/invite.html')

@bp.route('/join', methods=['POST'])
@login_required
def join_organization():
    user_id = session[SESSION_USER_ID]
    invite_code = request.form.get('invite_code', '').strip()

    if not invite_code:
        flash("Invite code is required.", "error")
        return redirect(url_for('profile.profile'))

    try:
        invite_ref = db.collection('invites').document(invite_code)
        invite = invite_ref.get()

        if not invite.exists:
            flash("Invalid invite code.", "error")
            return redirect(url_for('profile.profile'))

        org_id = invite.to_dict().get('organization_id')
        role = invite.to_dict().get('role')

        user_profile_ref = db.collection('player_profiles').document(user_id)
        user_profile_ref.update({
            'organization_id': org_id,
            'role': role
        })

        # Add user to the organization's member list
        org_ref = db.collection('organizations').document(org_id)
        org_ref.update({
            'members': db.ArrayUnion([user_id])
        })
        if role == 'instructor':
            org_ref.update({
                'instructors': db.ArrayUnion([user_id])
            })

        # Delete the invite code so it can't be reused
        invite_ref.delete()

        flash("Successfully joined organization!", "success")
    except Exception as e:
        logging.error(f"Error joining organization for user {user_id} with code {invite_code}: {e}")
        flash("An error occurred while joining the organization.", "error")

    return redirect(url_for('profile.profile'))